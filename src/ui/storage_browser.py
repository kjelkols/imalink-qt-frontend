"""
Storage Browser - Find and register existing storage locations
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTreeWidget, QTreeWidgetItem, QFileDialog,
                               QMessageBox, QProgressDialog, QTextEdit)
from PySide6.QtCore import Qt, QThread, Signal
from pathlib import Path
import json
from typing import List, Dict
from datetime import datetime


class StorageScannerWorker(QThread):
    """Worker thread for scanning directories for storage locations"""
    progress_updated = Signal(str, int, int)  # message, current, total
    storage_found = Signal(dict)  # storage info
    scan_completed = Signal(int)  # total found
    
    def __init__(self, scan_paths: List[str], options: dict):
        super().__init__()
        self.scan_paths = scan_paths
        self.options = options
        self.storages_found = []
        self._stop_requested = False
    
    def stop(self):
        """Request scan to stop"""
        self._stop_requested = True
    
    def run(self):
        """Scan directories for storage locations"""
        total_dirs = 0
        checked_dirs = 0
        
        try:
            # Count directories first (for progress)
            if self.options.get('estimate_progress', True):
                self.progress_updated.emit("Estimating scan size...", 0, 100)
                for root_path in self.scan_paths:
                    if self._stop_requested:
                        return
                    try:
                        total_dirs += sum(1 for _ in Path(root_path).rglob('*') if _.is_dir())
                    except Exception:
                        pass
            
            # Scan each path
            for root_path in self.scan_paths:
                if self._stop_requested:
                    break
                
                try:
                    self._scan_directory(root_path, checked_dirs, total_dirs)
                except Exception as e:
                    print(f"Error scanning {root_path}: {e}")
            
            self.scan_completed.emit(len(self.storages_found))
            
        except Exception as e:
            print(f"Scanner error: {e}")
            self.scan_completed.emit(len(self.storages_found))
    
    def _scan_directory(self, root_path: str, checked_dirs: int, total_dirs: int):
        """Recursively scan a directory"""
        root = Path(root_path)
        
        if not root.exists() or not root.is_dir():
            return
        
        max_depth = self.options.get('max_depth', 5)
        
        for dirpath in root.rglob('*'):
            if self._stop_requested:
                break
            
            if not dirpath.is_dir():
                continue
            
            # Check depth
            try:
                depth = len(dirpath.relative_to(root).parts)
                if depth > max_depth:
                    continue
            except ValueError:
                continue
            
            checked_dirs += 1
            if total_dirs > 0:
                progress = int((checked_dirs / total_dirs) * 100)
                self.progress_updated.emit(
                    f"Scanning: {dirpath}",
                    checked_dirs,
                    total_dirs
                )
            
            # Check for .imalink-storage signature file
            signature_file = dirpath / '.imalink-storage'
            if signature_file.exists():
                storage_info = self._parse_signature_file(signature_file)
                if storage_info:
                    self.storages_found.append(storage_info)
                    self.storage_found.emit(storage_info)
            
            # Check for legacy storage (imalink_* directories with index.json)
            if self.options.get('look_for_legacy', True):
                if dirpath.name.startswith('imalink_'):
                    index_file = dirpath / 'index.json'
                    if index_file.exists():
                        legacy_info = self._parse_legacy_storage(dirpath)
                        if legacy_info:
                            self.storages_found.append(legacy_info)
                            self.storage_found.emit(legacy_info)
    
    def _parse_signature_file(self, signature_path: Path) -> Dict:
        """Parse .imalink-storage signature file"""
        try:
            with open(signature_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            storage_dir = signature_path.parent
            
            # Get photo count and size
            photo_count = data.get('photo_count', 0)
            total_size = data.get('total_size_bytes', 0)
            
            return {
                'type': 'signature',
                'storage_uuid': data.get('storage_uuid'),
                'display_name': data.get('display_name', storage_dir.name),
                'base_path': str(storage_dir),
                'created_at': data.get('created_at'),
                'last_indexed': data.get('last_indexed'),
                'photo_count': photo_count,
                'total_size_bytes': total_size,
                'notes': data.get('notes', ''),
                'has_signature': True,
                'has_master_index': (storage_dir / 'imalink-master.json').exists(),
                'has_sessions': (storage_dir / 'imalink-sessions').exists()
            }
        except Exception as e:
            print(f"Error parsing signature file {signature_path}: {e}")
            return None
    
    def _parse_legacy_storage(self, storage_dir: Path) -> Dict:
        """Parse legacy storage directory"""
        try:
            index_file = storage_dir / 'index.json'
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Count photos
            photo_count = len(data.get('files', []))
            
            return {
                'type': 'legacy',
                'storage_uuid': None,  # Will be generated on import
                'display_name': storage_dir.name,
                'base_path': str(storage_dir),
                'created_at': None,
                'last_indexed': None,
                'photo_count': photo_count,
                'total_size_bytes': 0,
                'notes': 'Legacy storage (needs migration)',
                'has_signature': False,
                'has_master_index': False,
                'has_sessions': False,
                'is_legacy': True
            }
        except Exception as e:
            print(f"Error parsing legacy storage {storage_dir}: {e}")
            return None


class StorageBrowserDialog(QDialog):
    """Dialog for finding and registering storage locations"""
    
    def __init__(self, storage_manager, parent=None):
        super().__init__(parent)
        self.storage_manager = storage_manager
        self.scanner_worker = None
        self.found_storages = []
        
        self.setWindowTitle("Find Storage Locations")
        self.setMinimumSize(800, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🔍 Find ImaLink Storage Locations")
        header.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel(
            "Scan your computer for existing ImaLink storage locations.\n"
            "This will look for folders containing .imalink-storage signature files."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; color: #666;")
        layout.addWidget(instructions)
        
        # Scan paths section
        paths_layout = QHBoxLayout()
        
        paths_label = QLabel("Scan locations:")
        paths_layout.addWidget(paths_label)
        
        # Quick scan buttons
        home_btn = QPushButton("🏠 Home")
        home_btn.clicked.connect(lambda: self.add_scan_path(str(Path.home())))
        paths_layout.addWidget(home_btn)
        
        mnt_btn = QPushButton("💾 /mnt")
        mnt_btn.clicked.connect(lambda: self.add_scan_path("/mnt"))
        paths_layout.addWidget(mnt_btn)
        
        media_btn = QPushButton("📀 /media")
        media_btn.clicked.connect(lambda: self.add_scan_path("/media"))
        paths_layout.addWidget(media_btn)
        
        custom_btn = QPushButton("📁 Custom...")
        custom_btn.clicked.connect(self.add_custom_path)
        paths_layout.addWidget(custom_btn)
        
        paths_layout.addStretch()
        layout.addLayout(paths_layout)
        
        # Scan paths list
        self.paths_text = QTextEdit()
        self.paths_text.setMaximumHeight(80)
        self.paths_text.setPlaceholderText("Selected scan paths will appear here...")
        self.paths_text.setReadOnly(True)
        layout.addWidget(self.paths_text)
        
        # Scan button
        scan_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton("🔍 Start Scan")
        self.scan_btn.setStyleSheet("font-size: 12pt; padding: 10px;")
        self.scan_btn.clicked.connect(self.start_scan)
        scan_layout.addWidget(self.scan_btn)
        
        self.stop_btn = QPushButton("⏹ Stop Scan")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        scan_layout.addWidget(self.stop_btn)
        
        scan_layout.addStretch()
        layout.addLayout(scan_layout)
        
        # Results tree
        results_label = QLabel("Found storage locations:")
        results_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(results_label)
        
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels([
            "Name", "Path", "Photos", "Size", "Type", "Status"
        ])
        self.results_tree.setColumnWidth(0, 200)
        self.results_tree.setColumnWidth(1, 300)
        layout.addWidget(self.results_tree)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_none)
        button_layout.addWidget(select_none_btn)
        
        button_layout.addStretch()
        
        self.add_btn = QPushButton("Add Selected Storages")
        self.add_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        self.add_btn.clicked.connect(self.add_selected_storages)
        self.add_btn.setEnabled(False)
        button_layout.addWidget(self.add_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Initialize with home directory
        self.scan_paths = [str(Path.home())]
        self.update_paths_display()
    
    def add_scan_path(self, path: str):
        """Add a path to scan"""
        if path not in self.scan_paths:
            self.scan_paths.append(path)
            self.update_paths_display()
    
    def add_custom_path(self):
        """Add custom scan path"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Scan",
            str(Path.home())
        )
        
        if path:
            self.add_scan_path(path)
    
    def update_paths_display(self):
        """Update the paths text display"""
        self.paths_text.setPlainText("\n".join(self.scan_paths))
    
    def start_scan(self):
        """Start scanning for storage locations"""
        if not self.scan_paths:
            QMessageBox.warning(
                self,
                "No Paths Selected",
                "Please select at least one path to scan."
            )
            return
        
        # Clear previous results
        self.results_tree.clear()
        self.found_storages = []
        
        # Setup options
        options = {
            'max_depth': 5,
            'look_for_legacy': True,
            'estimate_progress': True
        }
        
        # Create and start worker
        self.scanner_worker = StorageScannerWorker(self.scan_paths, options)
        self.scanner_worker.progress_updated.connect(self.on_progress_updated)
        self.scanner_worker.storage_found.connect(self.on_storage_found)
        self.scanner_worker.scan_completed.connect(self.on_scan_completed)
        
        # Update UI
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.add_btn.setEnabled(False)
        
        # Start scan
        self.scanner_worker.start()
    
    def stop_scan(self):
        """Stop the current scan"""
        if self.scanner_worker:
            self.scanner_worker.stop()
            self.stop_btn.setEnabled(False)
    
    def on_progress_updated(self, message: str, current: int, total: int):
        """Update progress"""
        # Could add a progress bar here
        pass
    
    def on_storage_found(self, storage_info: dict):
        """Add found storage to tree"""
        self.found_storages.append(storage_info)
        
        # Create tree item
        item = QTreeWidgetItem(self.results_tree)
        item.setCheckState(0, Qt.Checked)  # Checked by default
        item.setText(0, storage_info['display_name'])
        item.setText(1, storage_info['base_path'])
        item.setText(2, str(storage_info['photo_count']))
        
        # Format size
        size_bytes = storage_info['total_size_bytes']
        if size_bytes > 1024**3:
            size_str = f"{size_bytes / 1024**3:.1f} GB"
        elif size_bytes > 1024**2:
            size_str = f"{size_bytes / 1024**2:.1f} MB"
        else:
            size_str = f"{size_bytes / 1024:.1f} KB"
        item.setText(3, size_str)
        
        # Type
        if storage_info.get('is_legacy'):
            item.setText(4, "⚠️ Legacy")
            item.setForeground(4, Qt.darkYellow)
        else:
            item.setText(4, "✅ Modern")
            item.setForeground(4, Qt.darkGreen)
        
        # Status
        if storage_info['has_signature']:
            item.setText(5, "Has signature")
        else:
            item.setText(5, "Needs migration")
            item.setForeground(5, Qt.darkYellow)
        
        # Store storage info in item
        item.setData(0, Qt.UserRole, storage_info)
        
        # Enable add button
        self.add_btn.setEnabled(True)
    
    def on_scan_completed(self, total_found: int):
        """Scan completed"""
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if total_found == 0:
            QMessageBox.information(
                self,
                "Scan Complete",
                "No storage locations found.\n\n"
                "Try scanning different paths or create a new storage location."
            )
        else:
            QMessageBox.information(
                self,
                "Scan Complete",
                f"Found {total_found} storage location(s).\n\n"
                "Select which ones to add and click 'Add Selected Storages'."
            )
    
    def select_all(self):
        """Select all items"""
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Checked)
    
    def select_none(self):
        """Deselect all items"""
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)
    
    def add_selected_storages(self):
        """Add selected storages to storage manager"""
        added = 0
        failed = 0
        
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            
            if item.checkState(0) == Qt.Checked:
                storage_info = item.data(0, Qt.UserRole)
                
                try:
                    # Register storage
                    storage_uuid = self.storage_manager.register_storage(
                        base_path=storage_info['base_path'],
                        display_name=storage_info['display_name']
                    )
                    
                    if storage_uuid:
                        added += 1
                        item.setText(5, "✅ Added")
                        item.setForeground(5, Qt.darkGreen)
                    else:
                        failed += 1
                        item.setText(5, "❌ Failed")
                        item.setForeground(5, Qt.red)
                        
                except Exception as e:
                    failed += 1
                    item.setText(5, f"❌ Error: {e}")
                    item.setForeground(5, Qt.red)
        
        # Show result
        if added > 0:
            QMessageBox.information(
                self,
                "Storages Added",
                f"Successfully added {added} storage location(s).\n"
                + (f"{failed} failed." if failed > 0 else "")
            )
            self.accept()  # Close dialog
        elif failed > 0:
            QMessageBox.warning(
                self,
                "Add Failed",
                f"Failed to add {failed} storage location(s)."
            )
