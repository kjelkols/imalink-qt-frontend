"""Register dialog for new user registration"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt


class RegisterDialog(QDialog):
    """User registration dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_data = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Register New User")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Create ImaLink Account")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username")
        layout.addWidget(self.username_input)
        
        # Email
        layout.addWidget(QLabel("Email:"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@example.com")
        layout.addWidget(self.email_input)
        
        # Display name
        layout.addWidget(QLabel("Display Name:"))
        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("Your full name")
        layout.addWidget(self.display_name_input)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Choose a strong password")
        layout.addWidget(self.password_input)
        
        # Confirm Password
        layout.addWidget(QLabel("Confirm Password:"))
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Re-enter password")
        layout.addWidget(self.confirm_password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        register_btn = QPushButton("Register")
        register_btn.setDefault(True)
        register_btn.clicked.connect(self._on_register)
        button_layout.addWidget(register_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect enter key
        self.confirm_password_input.returnPressed.connect(self._on_register)
    
    def _on_register(self):
        """Handle register button click"""
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        display_name = self.display_name_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        # Validation
        if not username:
            QMessageBox.warning(self, "Error", "Please enter username")
            return
        
        if not email:
            QMessageBox.warning(self, "Error", "Please enter email")
            return
        
        if '@' not in email:
            QMessageBox.warning(self, "Error", "Please enter a valid email address")
            return
        
        if not display_name:
            QMessageBox.warning(self, "Error", "Please enter display name")
            return
        
        if not password:
            QMessageBox.warning(self, "Error", "Please enter password")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return
        
        self.user_data = {
            "username": username,
            "email": email,
            "display_name": display_name,
            "password": password
        }
        self.accept()
    
    def get_user_data(self):
        """Get entered user data"""
        return self.user_data
