from smartparts.theme import CYAN, MINT, RED


def login_stylesheet() -> str:
    return f"""
    #canvas {{
        background: transparent;
        font-family: Arial;
    }}
    #brandPanel {{
        background: #0B1219;
        border-right: 1px solid #263948;
    }}
    #formZone {{
        background: #111A23;
    }}
    #accentBar {{
        border-radius: 2px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {CYAN}, stop:1 {MINT});
    }}
    #brandTitle {{
        color: #F2FAFF;
        font-size: 42px;
        font-weight: 700;
    }}
    #brandSubtitle {{
        color: #9EB4C3;
        font-size: 18px;
        line-height: 1.35;
    }}
    #diag1 {{
        background: rgba(45, 226, 230, 0.20);
        border-radius: 1px;
    }}
    #diag2 {{
        background: rgba(50, 246, 166, 0.40);
        border-radius: 1px;
    }}
    #diag3 {{
        background: rgba(108, 127, 140, 0.40);
        border-radius: 1px;
    }}
    #loginCard {{
        background: transparent;
    }}
    #formTitle {{
        color: #F4FAFF;
        font-size: 40px;
        font-weight: 700;
    }}
    #formCaption {{
        color: #8FA8B9;
        font-size: 16px;
    }}
    #errorBox {{
        background: #2A171B;
        border: 1px solid {RED};
        border-radius: 6px;
    }}
    #errorText {{
        color: #FFD4D8;
        font-size: 14px;
        font-weight: 600;
    }}
    #fieldLabel {{
        color: #B7CBD9;
        font-size: 14px;
        font-weight: 700;
    }}
    #loginInput,
    #passwordInput {{
        background: #0B141C;
        border: 1px solid rgba(45, 226, 230, 0.60);
        border-radius: 6px;
    }}
    #lineEdit {{
        color: #DDEAF2;
        background: transparent;
        font-size: 16px;
        selection-background-color: {CYAN};
        selection-color: #061116;
    }}
    #loginButton {{
        color: #061116;
        font-size: 16px;
        font-weight: 700;
        border: 1px solid #A9FFF0;
        border-radius: 6px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {CYAN}, stop:1 {MINT});
        padding: 0 18px;
    }}
    #loginButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5AF7FA, stop:1 #5DFFC0);
    }}
    #loginButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #19C9CD, stop:1 #25D98C);
    }}
    #footerText {{
        color: #8FA8B9;
        font-size: 11px;
    }}
    """


def dashboard_stylesheet() -> str:
    return f"""
    #dashboardCanvas {{
        background: transparent;
        font-family: Arial;
    }}
    #sidebar {{
        background: #0B1219;
        border-right: 1px solid #263948;
    }}
    #mainWorkspace {{
        background: #111A23;
    }}
    #brandAccent {{
        border-radius: 2px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {CYAN}, stop:1 {MINT});
    }}
    #brandTitle {{
        color: #F2FAFF;
        font-size: 28px;
        font-weight: 700;
    }}
    #brandSubtitle,
    #pageSubtitle,
    #cardDescription,
    #summarySubtitle {{
        color: #8FA8B9;
    }}
    #sessionTitle {{
        color: {CYAN};
        font-size: 13px;
        font-weight: 700;
    }}
    #sessionCard,
    #summaryPanel {{
        background: #0F1B24;
        border: 1px solid #263948;
        border-radius: 8px;
    }}
    #operatorText,
    #logoutText,
    #taskLabel {{
        color: #DDEAF2;
        font-weight: 700;
    }}
    #sessionRoleText {{
        color: #8FA8B9;
        font-size: 12px;
        font-weight: 600;
    }}
    #logoutButton,
    #secondaryAction {{
        background: #132531;
        border: 1px solid rgba(45, 226, 230, 0.55);
        border-radius: 6px;
    }}
    #logoutButton:hover,
    #secondaryAction:hover {{
        background: #173242;
        border-color: rgba(50, 246, 166, 0.75);
    }}
    #pageTitle {{
        color: #F4FAFF;
        font-size: 34px;
        font-weight: 700;
    }}
    #quickSearch {{
        background: #0B141C;
        border: 1px solid rgba(45, 226, 230, 0.60);
        border-radius: 6px;
    }}
    #searchInput {{
        color: #DDEAF2;
        background: transparent;
        border: none;
        font-size: 15px;
        selection-background-color: {CYAN};
        selection-color: #061116;
    }}
    #modeCard {{
        background: #101B24;
        border: 1px solid #263948;
        border-radius: 8px;
    }}
    #modeCardPrimary {{
        background: #101B24;
        border: 1px solid rgba(45, 226, 230, 0.40);
        border-radius: 8px;
    }}
    #modeCardAccent {{
        background: #101B24;
        border: 1px solid rgba(50, 246, 166, 0.40);
        border-radius: 8px;
    }}
    #cardTitle,
    #summaryTitle {{
        color: #F4FAFF;
        font-weight: 700;
    }}
    #primaryAction {{
        color: #061116;
        font-size: 14px;
        font-weight: 700;
        border: 1px solid #A9FFF0;
        border-radius: 6px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {CYAN}, stop:1 {MINT});
    }}
    #primaryAction:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5AF7FA, stop:1 #5DFFC0);
    }}
    #secondaryAction {{
        color: #DFFDF5;
        font-size: 14px;
        font-weight: 700;
    }}
    #taskItem {{
        background: #111F29;
        border: 1px solid #263948;
        border-radius: 5px;
    }}
    #taskItemProblem {{
        background: #2A171B;
        border: 1px solid {RED};
        border-radius: 5px;
    }}
    #taskCountMint {{
        color: {MINT};
        font-size: 18px;
        font-weight: 700;
    }}
    #taskCountCyan {{
        color: {CYAN};
        font-size: 18px;
        font-weight: 700;
    }}
    #taskCountRed,
    #taskProblemLabel {{
        color: #FF7A85;
        font-size: 18px;
        font-weight: 700;
    }}
    """
