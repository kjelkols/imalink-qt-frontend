"""
Login Dialog for ImaLink
Handles user authentication with login and registration
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QMessageBox, QTabWidget, QWidget, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from typing import Optional


class LoginDialog(QDialog):
    """
    Login/Register dialog for user authentication
    Emits login_success signal with token and user data on successful login
    """
    
    login_success = Signal(str, dict)  # token, user_data
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.token: Optional[str] = None
        self.user_data: Optional[dict] = None
        
        self.setWindowTitle("ImaLink - Login")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("ImaLink Photo Manager")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Innlogging kreves for å fortsette")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Tab widget for Login/Register
        tabs = QTabWidget()
        
        # Login tab
        login_widget = self.create_login_tab()
        tabs.addTab(login_widget, "Logg inn")
        
        # Register tab
        register_widget = self.create_register_tab()
        tabs.addTab(register_widget, "Ny bruker")
        
        layout.addWidget(tabs)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #d32f2f; margin-top: 10px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
    
    def create_login_tab(self) -> QWidget:
        """Create the login tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Form layout
        form = QFormLayout()
        form.setSpacing(15)
        
        # Username
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Brukernavn")
        self.login_username.returnPressed.connect(self.on_login)
        form.addRow("Brukernavn:", self.login_username)
        
        # Password
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setPlaceholderText("Passord")
        self.login_password.returnPressed.connect(self.on_login)
        form.addRow("Passord:", self.login_password)
        
        layout.addLayout(form)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Husk meg på denne datamaskinen")
        self.remember_checkbox.setChecked(True)
        layout.addWidget(self.remember_checkbox)
        
        # Login button
        login_btn = QPushButton("Logg inn")
        login_btn.clicked.connect(self.on_login)
        login_btn.setDefault(True)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        layout.addWidget(login_btn)
        
        layout.addStretch()
        
        return widget
    
    def create_register_tab(self) -> QWidget:
        """Create the registration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Form layout
        form = QFormLayout()
        form.setSpacing(15)
        
        # Username
        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Velg et brukernavn")
        form.addRow("Brukernavn:", self.reg_username)
        
        # Email
        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("din@epost.no")
        form.addRow("E-post:", self.reg_email)
        
        # Display name
        self.reg_display_name = QLineEdit()
        self.reg_display_name.setPlaceholderText("Ditt fulle navn")
        form.addRow("Visningsnavn:", self.reg_display_name)
        
        # Password
        self.reg_password = QLineEdit()
        self.reg_password.setEchoMode(QLineEdit.Password)
        self.reg_password.setPlaceholderText("Velg et sikkert passord")
        form.addRow("Passord:", self.reg_password)
        
        # Confirm password
        self.reg_confirm_password = QLineEdit()
        self.reg_confirm_password.setEchoMode(QLineEdit.Password)
        self.reg_confirm_password.setPlaceholderText("Gjenta passordet")
        self.reg_confirm_password.returnPressed.connect(self.on_register)
        form.addRow("Bekreft passord:", self.reg_confirm_password)
        
        layout.addLayout(form)
        
        # Register button
        register_btn = QPushButton("Opprett bruker")
        register_btn.clicked.connect(self.on_register)
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #2e7d32;
            }
            QPushButton:pressed {
                background-color: #1b5e20;
            }
        """)
        layout.addWidget(register_btn)
        
        layout.addStretch()
        
        return widget
    
    def on_login(self):
        """Handle login button click"""
        username = self.login_username.text().strip()
        password = self.login_password.text()
        
        if not username or not password:
            self.show_error("Vennligst fyll inn både brukernavn og passord")
            return
        
        self.status_label.setText("Logger inn...")
        self.status_label.setStyleSheet("color: #1976d2;")
        
        try:
            # Call API client login method
            response = self.api_client.login(username, password)
            
            self.token = response['access_token']
            self.user_data = response['user']
            
            # Emit success signal
            self.login_success.emit(self.token, self.user_data)
            
            # Close dialog
            self.accept()
            
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                self.show_error("Feil brukernavn eller passord")
            elif "404" in error_msg:
                self.show_error("Kunne ikke koble til server")
            else:
                self.show_error(f"Innlogging feilet: {error_msg}")
    
    def on_register(self):
        """Handle register button click"""
        print("🔧 DEBUG LoginDialog: on_register called")
        username = self.reg_username.text().strip()
        email = self.reg_email.text().strip()
        display_name = self.reg_display_name.text().strip()
        password = self.reg_password.text()
        confirm = self.reg_confirm_password.text()
        
        print(f"🔧 DEBUG LoginDialog: Registration data - username={username}, email={email}, display_name={display_name}")
        
        # Validation
        if not username or not email or not display_name or not password:
            print("🔧 DEBUG LoginDialog: Validation failed - missing fields")
            self.show_error("Vennligst fyll inn alle feltene")
            return
        
        if password != confirm:
            print("🔧 DEBUG LoginDialog: Validation failed - passwords don't match")
            self.show_error("Passordene matcher ikke")
            return
        
        if len(password) < 6:
            print("🔧 DEBUG LoginDialog: Validation failed - password too short")
            self.show_error("Passordet må være minst 6 tegn")
            return
        
        if "@" not in email or "." not in email:
            print("🔧 DEBUG LoginDialog: Validation failed - invalid email")
            self.show_error("Ugyldig e-postadresse")
            return
        
        print("🔧 DEBUG LoginDialog: Validation passed - calling API register...")
        self.status_label.setText("Oppretter bruker...")
        self.status_label.setStyleSheet("color: #1976d2;")
        
        try:
            # Call API client register method
            print(f"🔧 DEBUG LoginDialog: Calling api_client.register...")
            response = self.api_client.register(
                username=username,
                email=email,
                password=password,
                display_name=display_name
            )
            
            print(f"🔧 DEBUG LoginDialog: Registration successful! Response: {response}")
            
            # Show success message
            QMessageBox.information(
                self,
                "Bruker opprettet",
                f"Brukeren '{username}' er nå opprettet!\n\nDu kan nå logge inn med ditt brukernavn og passord."
            )
            
            print("🔧 DEBUG LoginDialog: Switching to login tab...")
            # Switch to login tab and pre-fill username
            self.login_username.setText(username)
            self.login_password.setFocus()
            
            # Find and switch to login tab
            tabs = self.findChild(QTabWidget)
            if tabs:
                tabs.setCurrentIndex(0)
            
            self.status_label.setText("")
            
        except Exception as e:
            print(f"🔧 DEBUG LoginDialog: Registration failed with exception: {type(e).__name__}: {e}")
            error_msg = str(e)
            if "409" in error_msg or "already exists" in error_msg.lower():
                self.show_error("Brukernavnet er allerede tatt")
            elif "400" in error_msg:
                self.show_error("Ugyldig input. Sjekk alle feltene.")
            else:
                self.show_error(f"Registrering feilet: {error_msg}")
    
    def show_error(self, message: str):
        """Display error message"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #d32f2f; margin-top: 10px;")
    
    def get_remember_me(self) -> bool:
        """Check if user wants to be remembered"""
        return self.remember_checkbox.isChecked()
