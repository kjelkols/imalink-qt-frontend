"""Login dialog for user authentication"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt


class LoginDialog(QDialog):
    """Simple login dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.username_value = None
        self.password_value = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("ImaLink Login")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Login to ImaLink")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        layout.addWidget(self.username_input)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        layout.addWidget(self.password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        register_btn = QPushButton("Register...")
        register_btn.clicked.connect(self._on_register)
        button_layout.addWidget(register_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        login_btn = QPushButton("Login")
        login_btn.setDefault(True)
        login_btn.clicked.connect(self._on_login)
        button_layout.addWidget(login_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect enter key
        self.password_input.returnPressed.connect(self._on_login)
    
    def _on_login(self):
        """Handle login button click"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username:
            QMessageBox.warning(self, "Error", "Please enter username")
            return
        
        if not password:
            QMessageBox.warning(self, "Error", "Please enter password")
            return
        
        self.username_value = username
        self.password_value = password
        self.accept()
    
    def get_credentials(self):
        """Get entered credentials"""
        return self.username_value, self.password_value
    
    def _on_register(self):
        """Show register dialog"""
        from .register_dialog import RegisterDialog
        
        register_dialog = RegisterDialog(self)
        if register_dialog.exec() == QDialog.Accepted:
            user_data = register_dialog.get_user_data()
            if user_data:
                # Try to register with backend
                try:
                    api_client = getattr(self, 'api_client', None)
                    if api_client:
                        api_client.register(
                            username=user_data["username"],
                            email=user_data["email"],
                            password=user_data["password"],
                            display_name=user_data["display_name"]
                        )
                        # Success - fill in credentials for login
                        self.username_input.setText(user_data["username"])
                        self.password_input.setText(user_data["password"])
                        QMessageBox.information(
                            self,
                            "Registration Successful",
                            f"Account created for {user_data['display_name']}!\n\nYou can now login."
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Error",
                            "API client not available. Cannot register."
                        )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Registration Failed",
                        f"Could not create account:\n{e}"
                    )
