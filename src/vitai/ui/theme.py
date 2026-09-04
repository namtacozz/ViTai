from __future__ import annotations

def get_stylesheet(theme: str = "dark") -> str:
    if theme == "light":
        return """
        QDialog {
            background-color: #F8FAFC;
            color: #0F172A;
            font-family: 'Segoe UI', system-ui, -apple-system, 'DejaVu Sans', sans-serif;
            font-size: 14px;
        }

        /* Tables */
        QTableWidget {
            background-color: #FFFFFF;
            color: #0F172A;
            gridline-color: #E2E8F0;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            selection-background-color: rgba(224, 159, 94, 0.2);
            selection-color: #0F172A;
        }
        QTableCornerButton::section {
            background-color: #F1F5F9;
            border: 1px solid #E2E8F0;
        }
        QHeaderView {
            background-color: #F1F5F9;
            border: none;
        }
        QHeaderView::section {
            background-color: #F1F5F9;
            color: #475569;
            padding: 6px 8px;
            border: 1px solid #E2E8F0;
            font-weight: 700;
            font-size: 12px;
        }
        QHeaderView::section:vertical {
            background-color: #F1F5F9;
            color: #475569;
            border: 1px solid #E2E8F0;
        }

        /* Menus */
        QMenu {
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            padding: 4px;
        }
        QMenu::item {
            padding: 6px 16px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background-color: rgba(224, 159, 94, 0.2);
            color: #B45309;
        }

        /* Sidebar */
        QFrame#sidebarFrame {
            background-color: #F1F5F9;
            border-right: 1px solid #E2E8F0;
        }

        QLabel#brandTitle {
            color: #0F172A;
            font-size: 16px;
            font-weight: 800;
        }

        QLabel#brandVer {
            color: #64748B;
            font-size: 11px;
            font-weight: 600;
        }

        QListWidget#sidebarMenu {
            background-color: transparent;
            border: none;
            outline: none;
            padding: 4px;
        }

        QListWidget#sidebarMenu::item {
            color: #334155;
            padding: 10px 12px;
            border-radius: 8px;
            margin-bottom: 5px;
            font-weight: 700;
            font-size: 15px;
        }

        QListWidget#sidebarMenu::item:hover {
            background-color: #E2E8F0;
            color: #0F172A;
        }

        QListWidget#sidebarMenu::item:selected {
            background-color: rgba(224, 159, 94, 0.18);
            color: #B45309;
            border-left: 3px solid #E09F5E;
            font-weight: 800;
        }

        /* Cards */
        QFrame#cardFrame {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
        }

        QLabel#cardTitle {
            color: #0F172A;
            font-weight: 700;
            font-size: 15px;
        }

        QLabel#cardDesc {
            color: #64748B;
            font-size: 13px;
        }

        QLabel#headerTitle {
            color: #0F172A;
            font-size: 20px;
            font-weight: 800;
        }

        /* Login Gate Overlay */
        QFrame#loginGateOverlay {
            background-color: rgba(241, 245, 249, 0.96);
        }
        QFrame#loginCard {
            background-color: #FFFFFF;
            border: 1.5px solid rgba(224, 159, 94, 0.45);
            border-radius: 16px;
        }

        QLabel {
            color: #1E293B;
            font-size: 14px;
        }

        /* Inputs & Combos */
        QLineEdit, QComboBox {
            background-color: #F8FAFC;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 6px 12px;
            color: #0F172A;
            min-height: 28px;
            font-size: 14px;
        }

        QLineEdit:focus, QComboBox:focus, QComboBox:hover {
            border-color: #E09F5E;
        }

        QComboBox QAbstractItemView {
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            selection-background-color: rgba(224, 159, 94, 0.18);
            selection-color: #B45309;
            padding: 6px;
            outline: none;
        }

        /* Checkbox */
        QCheckBox {
            spacing: 8px;
            color: #1E293B;
            font-size: 14px;
            font-weight: 500;
        }

        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 5px;
            border: 1px solid #CBD5E1;
            background-color: #F8FAFC;
        }

        QCheckBox::indicator:checked {
            background-color: #E09F5E;
            border-color: #E09F5E;
        }

        /* Buttons */
        QPushButton {
            background-color: #F1F5F9;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 7px 14px;
            color: #0F172A;
            font-weight: 600;
            font-size: 13px;
        }

        QPushButton:hover {
            background-color: #E2E8F0;
            border-color: #94A3B8;
        }

        QPushButton#themeToggleBtn {
            background-color: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            color: #0F172A;
            font-size: 16px;
            padding: 2px;
        }
        QPushButton#themeToggleBtn:hover {
            background-color: #F1F5F9;
            border-color: #E09F5E;
        }

        QPushButton#saveButton {
            background-color: #E09F5E;
            color: #0F172A;
            border: none;
            border-radius: 8px;
            font-weight: 800;
            font-size: 14px;
            padding: 9px 18px;
        }
        QPushButton#saveButton:hover {
            background-color: #ECAB6D;
        }

        QPushButton#applyButton {
            background-color: #F1F5F9;
            color: #B45309;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 7px 14px;
            font-weight: 600;
            font-size: 13px;
        }
        QPushButton#applyButton:hover {
            background-color: #E2E8F0;
            border-color: #E09F5E;
        }

        QPushButton#exitButton {
            background-color: transparent;
            color: #DC2626;
            border: 1px solid #FECACA;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            padding: 6px 12px;
        }
        QPushButton#exitButton:hover {
            background-color: #FEE2E2;
            color: #B91C1C;
        }

        QPushButton#oauthButton {
            background-color: rgba(224, 159, 94, 0.14);
            color: #B45309;
            border: 1px solid #E09F5E;
            font-size: 13px;
            font-weight: 700;
            border-radius: 8px;
            padding: 7px 14px;
        }
        QPushButton#oauthButton:hover {
            background-color: #E09F5E;
            color: #0F172A;
        }

        QPushButton#logoutButton {
            background-color: #FEF2F2;
            color: #DC2626;
            border: 1px solid #FECACA;
            border-radius: 8px;
            font-size: 12px;
            padding: 6px 10px;
        }
        QPushButton#logoutButton:hover {
            background-color: #FEE2E2;
        }

        QPushButton#refreshButton {
            background-color: #F1F5F9;
            color: #B45309;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            font-size: 13px;
            font-weight: bold;
            padding: 6px 12px;
        }
        QPushButton#refreshButton:hover {
            background-color: #E2E8F0;
            border-color: #E09F5E;
        }

        QPushButton#hotkeyButton {
            background-color: #F1F5F9;
            color: #B45309;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 700;
            padding: 8px 16px;
        }
        QPushButton#hotkeyButton:hover {
            background-color: #E2E8F0;
            border-color: #E09F5E;
        }

        QPushButton#testButton {
            background-color: rgba(16, 185, 129, 0.12);
            color: #059669;
            border: 1px solid #10B981;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            padding: 7px 14px;
        }
        QPushButton#testButton:hover {
            background-color: #059669;
            color: #FFFFFF;
        }

        QPushButton#helpButton {
            background-color: #F1F5F9;
            color: #4F46E5;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            font-size: 13px;
            padding: 7px 12px;
        }
        QPushButton#helpButton:hover {
            background-color: #EEF2FF;
            border-color: #6366F1;
        }

        /* Buttons and Elements */

        QPushButton#cardToolBtn {
            background-color: transparent;
            border: none;
            color: #64748B;
            font-size: 12px;
            padding: 2px;
            min-width: 18px;
        }
        QPushButton#cardToolBtn:hover {
            color: #B45309;
            background-color: rgba(224, 159, 94, 0.12);
            border-radius: 4px;
        }

        QPushButton#cardDelBtn {
            background-color: transparent;
            border: none;
            color: #EF4444;
            font-size: 12px;
            padding: 2px;
            min-width: 18px;
        }
        QPushButton#cardDelBtn:hover {
            color: #DC2626;
            background-color: rgba(239, 68, 68, 0.12);
            border-radius: 4px;
        }

        QPushButton#switchBtnOn {
            background-color: #E09F5E;
            color: #0F172A;
            border: 1px solid #E09F5E;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 800;
            padding: 2px 8px;
            min-width: 38px;
        }
        QPushButton#switchBtnOff {
            background-color: #E2E8F0;
            color: #64748B;
            border: 1px solid #CBD5E1;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            min-width: 38px;
        }

        QProgressBar {
            background-color: #E2E8F0;
            border: none;
            border-radius: 3px;
            max-height: 5px;
            min-height: 5px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #10B981;
            border-radius: 3px;
        }

        QScrollBar:vertical {
            background: transparent;
            width: 6px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #CBD5E1;
            border-radius: 3px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #94A3B8;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background: none;
            height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }

        QPlainTextEdit#logView {
            background-color: #FFFFFF;
            color: #1E293B;
            font-family: 'Consolas', 'Fira Code', 'DejaVu Sans Mono', monospace;
            font-size: 12px;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 10px;
            line-height: 1.4;
        }
        """

    # Dark Theme (9Router Carbon & Warm Amber)
    return """
    QDialog {
        background-color: #0C0D0E;
        color: #F1F5F9;
        font-family: 'Segoe UI', system-ui, -apple-system, 'DejaVu Sans', sans-serif;
        font-size: 14px;
    }

    /* Tables */
    QTableWidget {
        background-color: #121316;
        color: #EDEDED;
        gridline-color: #1F2228;
        border: 1px solid #1F2228;
        border-radius: 8px;
        selection-background-color: rgba(224, 159, 94, 0.25);
        selection-color: #FFFFFF;
    }
    QTableCornerButton::section {
        background-color: #181A1F;
        border: 1px solid #1F2228;
    }
    QHeaderView {
        background-color: #181A1F;
        border: none;
    }
    QHeaderView::section {
        background-color: #181A1F;
        color: #94A3B8;
        padding: 6px 8px;
        border: 1px solid #1F2228;
        font-weight: 700;
        font-size: 12px;
    }
    QHeaderView::section:vertical {
        background-color: #181A1F;
        color: #94A3B8;
        border: 1px solid #1F2228;
    }

    /* Menus */
    QMenu {
        background-color: #121316;
        color: #EDEDED;
        border: 1px solid #27272A;
        border-radius: 6px;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 16px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: rgba(224, 159, 94, 0.25);
        color: #E09F5E;
    }

    /* Left Sidebar */
    QFrame#sidebarFrame {
        background-color: #121316;
        border-right: 1px solid #1F2228;
    }

    QLabel#brandTitle {
        color: #F8FAFC;
        font-size: 16px;
        font-weight: 800;
    }

    QLabel#brandVer {
        color: #94A3B8;
        font-size: 11px;
        font-weight: 600;
    }

    QListWidget#sidebarMenu {
        background-color: transparent;
        border: none;
        outline: none;
        padding: 4px;
    }

    QListWidget#sidebarMenu::item {
        color: #94A3B8;
        padding: 10px 12px;
        border-radius: 8px;
        margin-bottom: 5px;
        font-weight: 700;
        font-size: 15px;
    }

    QListWidget#sidebarMenu::item:hover {
        background-color: #181A1F;
        color: #F8FAFC;
    }

    QListWidget#sidebarMenu::item:selected {
        background-color: rgba(224, 159, 94, 0.14);
        color: #E09F5E;
        border-left: 3px solid #E09F5E;
        font-weight: 800;
    }

    /* Card Panels */
    QFrame#cardFrame {
        background-color: #181A1F;
        border: 1px solid #23272F;
        border-radius: 10px;
    }

    QLabel#cardTitle {
        color: #F8FAFC;
        font-weight: 700;
        font-size: 15px;
    }

    QLabel#cardDesc {
        color: #94A3B8;
        font-size: 13px;
    }

    QLabel#headerTitle {
        color: #F8FAFC;
        font-size: 20px;
        font-weight: 800;
    }

    QLabel#headerDesc {
        color: #94A3B8;
        font-size: 13px;
    }

    /* Login Gate Overlay */
    QFrame#loginGateOverlay {
        background-color: rgba(12, 13, 14, 0.95);
    }
    QFrame#loginCard {
        background-color: #141619;
        border: 1.5px solid rgba(224, 159, 94, 0.4);
        border-radius: 16px;
    }

    QLabel {
        color: #E2E8F0;
        font-size: 14px;
    }

    /* Inputs and Combos */
    QLineEdit, QComboBox {
        background-color: #111215;
        border: 1px solid #242831;
        border-radius: 8px;
        padding: 6px 12px;
        color: #F1F5F9;
        min-height: 28px;
        font-size: 14px;
    }

    QLineEdit:focus, QComboBox:focus, QComboBox:hover {
        border-color: #E09F5E;
    }

    QComboBox QAbstractItemView {
        background-color: #181A1F;
        color: #F1F5F9;
        border: 1px solid #23272F;
        selection-background-color: rgba(224, 159, 94, 0.2);
        selection-color: #E09F5E;
        padding: 6px;
        outline: none;
    }

    /* Checkboxes / Switches */
    QCheckBox {
        spacing: 8px;
        color: #E2E8F0;
        font-size: 14px;
        font-weight: 500;
    }

    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 5px;
        border: 1px solid #333842;
        background-color: #111215;
    }

    QCheckBox::indicator:checked {
        background-color: #E09F5E;
        border-color: #E09F5E;
    }

    /* Buttons */
    QPushButton {
        background-color: #1C1F26;
        border: 1px solid #282D38;
        border-radius: 8px;
        padding: 7px 14px;
        color: #E2E8F0;
        font-weight: 600;
        font-size: 13px;
    }

    QPushButton:hover {
        background-color: #252A34;
        border-color: #475569;
        color: #FFFFFF;
    }

    QPushButton#themeToggleBtn {
        background-color: #181A1F;
        border: 1px solid #23272F;
        border-radius: 8px;
        color: #E09F5E;
        font-size: 16px;
        padding: 2px;
    }
    QPushButton#themeToggleBtn:hover {
        background-color: #23272F;
        border-color: #E09F5E;
    }

    /* Primary Save Button */
    QPushButton#saveButton {
        background-color: #E09F5E;
        color: #0C0D0E;
        border: none;
        border-radius: 8px;
        font-weight: 800;
        font-size: 14px;
        padding: 9px 18px;
    }

    QPushButton#saveButton:hover {
        background-color: #ECAB6D;
    }

    /* Apply Button */
    QPushButton#applyButton {
        background-color: #1C1F26;
        color: #E09F5E;
        border: 1px solid #2D3340;
        border-radius: 8px;
        padding: 7px 14px;
        font-weight: 600;
        font-size: 13px;
    }

    QPushButton#applyButton:hover {
        background-color: #262C37;
        border-color: #E09F5E;
    }

    /* Exit Button */
    QPushButton#exitButton {
        background-color: transparent;
        color: #F87171;
        border: 1px solid #451A1A;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        padding: 6px 12px;
    }

    QPushButton#exitButton:hover {
        background-color: #451A1A;
        color: #FFFFFF;
    }

    /* OAuth Button */
    QPushButton#oauthButton {
        background-color: rgba(224, 159, 94, 0.14);
        color: #E09F5E;
        border: 1px solid #E09F5E;
        font-size: 13px;
        font-weight: 700;
        border-radius: 8px;
        padding: 7px 14px;
    }

    QPushButton#oauthButton:hover {
        background-color: #E09F5E;
        color: #0C0D0E;
    }

    QPushButton#logoutButton {
        background-color: #2A1820;
        color: #F87171;
        border: 1px solid #5C222E;
        border-radius: 8px;
        font-size: 12px;
        padding: 6px 10px;
    }

    QPushButton#logoutButton:hover {
        background-color: #5C222E;
        color: #FFFFFF;
    }

    QPushButton#refreshButton {
        background-color: #1C1F26;
        color: #E09F5E;
        border: 1px solid #282D38;
        border-radius: 8px;
        font-size: 13px;
        font-weight: bold;
        padding: 6px 12px;
    }

    QPushButton#refreshButton:hover {
        background-color: #252A34;
        border-color: #E09F5E;
    }

    QPushButton#hotkeyButton {
        background-color: #181A1F;
        color: #E09F5E;
        border: 1px solid #23272F;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 700;
        padding: 8px 16px;
    }

    QPushButton#hotkeyButton:hover {
        background-color: #23272F;
        border-color: #E09F5E;
    }

    QPushButton#testButton {
        background-color: rgba(34, 197, 94, 0.12);
        color: #4ADE80;
        border: 1px solid #22C55E;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        padding: 7px 14px;
    }

    QPushButton#testButton:hover {
        background-color: #22C55E;
        color: #0C0D0E;
    }

    QPushButton#helpButton {
        background-color: #1C1F26;
        color: #A5B4FC;
        border: 1px solid #282D38;
        border-radius: 8px;
        font-size: 13px;
        padding: 7px 12px;
    }

    QPushButton#helpButton:hover {
        background-color: #252A34;
        border-color: #6366F1;
    }

    /* Dark Mode Buttons and Elements */

    QPushButton#cardToolBtn {
        background-color: transparent;
        border: none;
        color: #94A3B8;
        font-size: 12px;
        padding: 2px;
        min-width: 18px;
    }
    QPushButton#cardToolBtn:hover {
        color: #E09F5E;
        background-color: rgba(224, 159, 94, 0.12);
        border-radius: 4px;
    }

    QPushButton#cardDelBtn {
        background-color: transparent;
        border: none;
        color: #EF4444;
        font-size: 12px;
        padding: 2px;
        min-width: 18px;
    }
    QPushButton#cardDelBtn:hover {
        color: #F87171;
        background-color: rgba(239, 68, 68, 0.12);
        border-radius: 4px;
    }

    QPushButton#switchBtnOn {
        background-color: #E09F5E;
        color: #0C0D0E;
        border: 1px solid #E09F5E;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 800;
        padding: 2px 8px;
        min-width: 38px;
    }
    QPushButton#switchBtnOff {
        background-color: #23272F;
        color: #94A3B8;
        border: 1px solid #333842;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        min-width: 38px;
    }

    QProgressBar {
        background-color: #23272F;
        border: none;
        border-radius: 3px;
        max-height: 5px;
        min-height: 5px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #22C55E;
        border-radius: 3px;
    }

    QScrollBar:vertical {
        background: transparent;
        width: 6px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #2D3340;
        border-radius: 3px;
        min-height: 20px;
    }
    QScrollBar::handle:vertical:hover {
        background: #475569;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }

    QPlainTextEdit#logView {
        background-color: #08090A;
        color: #CBD5E1;
        font-family: 'JetBrains Mono', 'Consolas', 'Fira Code', monospace;
        font-size: 12px;
        border: 1px solid #1F2228;
        border-radius: 8px;
        padding: 10px;
        line-height: 1.4;
    }
    """


