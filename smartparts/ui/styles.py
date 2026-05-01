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
    #brandsLoadingStatus {{
        background: #101B24;
        border: 1px solid rgba(45, 226, 230, 0.55);
        border-radius: 8px;
    }}
    #brandsLoadingTitle {{
        color: #DDEAF2;
        font-size: 13px;
        font-weight: 700;
    }}
    #brandsLoadingSubtitle {{
        color: #8FA8B9;
        font-size: 11px;
        font-weight: 600;
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
    #primaryAction:disabled,
    #secondaryAction:disabled {{
        color: #6F8493;
        background: #10202A;
        border: 1px solid #263948;
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


def order_creation_stylesheet() -> str:
    return f"""
    #orderCanvas {{
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
    #brandTitle,
    #pageTitle,
    #panelTitle {{
        color: #F4FAFF;
        font-weight: 700;
    }}
    #brandTitle {{
        font-size: 28px;
    }}
    #brandSubtitle,
    #pageSubtitle,
    #mutedText,
    #fieldLabel,
    #tableHead,
    #hintText {{
        color: #8FA8B9;
    }}
    #sessionTitle,
    #hintTitle {{
        color: {CYAN};
        font-size: 13px;
        font-weight: 700;
    }}
    #sessionCard,
    #formPanel,
    #productsPanel,
    #totalsPanel,
    #hintBox {{
        background: #101B24;
        border: 1px solid #263948;
        border-radius: 8px;
    }}
    #sessionCard {{
        background: #0F1B24;
    }}
    #navActive,
    #navButton,
    #secondaryAction,
    #backToDashboardButton,
    #newDocumentButton {{
        background: #132531;
        border: 1px solid rgba(45, 226, 230, 0.55);
        border-radius: 6px;
    }}
    #navButton {{
        background: transparent;
        border: none;
        color: #8FA8B9;
        font-size: 14px;
        font-weight: 600;
        text-align: left;
        padding: 0 12px;
    }}
    #navActive {{
        color: #F4FAFF;
        font-size: 14px;
        font-weight: 700;
        text-align: left;
        padding: 0 12px;
    }}
    #logoutButton,
    #secondaryAction,
    #backToDashboardButton,
    #newDocumentButton {{
        color: #DDEAF2;
        font-size: 13px;
        font-weight: 700;
    }}
    #pageTitle {{
        font-size: 28px;
    }}
    #pageSubtitle {{
        font-size: 14px;
    }}
    #fieldLabel {{
        font-size: 12px;
        font-weight: 700;
    }}
    #inputShell,
    #searchShell,
    #toggleInactive,
    #productInput,
    #productInputAccent {{
        background: #0B141C;
        border: 1px solid #263948;
        border-radius: 6px;
    }}
    #productInputAccent {{
        border-color: {CYAN};
    }}
    #searchShell {{
        border-color: rgba(45, 226, 230, 0.42);
    }}
    #lineEdit {{
        color: #F4FAFF;
        background: transparent;
        border: none;
        font-size: 14px;
        selection-background-color: {CYAN};
        selection-color: #061116;
    }}
    #lineEdit[accentText="true"] {{
        color: {MINT};
        font-weight: 700;
    }}
    #comboBox {{
        color: #F4FAFF;
        background: #0B141C;
        border: 1px solid #263948;
        border-radius: 6px;
        padding: 0 10px;
        font-size: 13px;
        font-weight: 700;
    }}
    #comboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    #comboBox QAbstractItemView {{
        color: #F4FAFF;
        background: #0B1219;
        border: 1px solid #263948;
        selection-background-color: rgba(45, 226, 230, 0.24);
    }}
    #toggleActive {{
        color: #F4FAFF;
        font-size: 13px;
        font-weight: 700;
        background: rgba(45, 226, 230, 0.14);
        border: 1px solid {CYAN};
        border-radius: 6px;
    }}
    #toggleInactive {{
        color: #8FA8B9;
        font-size: 13px;
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
    #productOverlay {{
        background: rgba(5, 10, 14, 0.72);
    }}
    #productAddWindow {{
        background: #111A23;
        border: 1px solid #263948;
        border-radius: 8px;
    }}
    #productAddPanel {{
        background: #101B24;
        border: 1px solid #263948;
        border-radius: 8px;
    }}
    #productSearchShell {{
        background: #0B141C;
        border: 1px solid rgba(45, 226, 230, 0.55);
        border-radius: 6px;
    }}
    #sectionAccentTitle {{
        color: {CYAN};
        font-size: 13px;
        font-weight: 700;
    }}
    #productResult,
    #productResultActive {{
        color: #DDEAF2;
        background: #0F1B24;
        border: 1px solid #263948;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        text-align: left;
        padding: 10px 12px;
    }}
    #productResultActive {{
        background: #122632;
        border-color: rgba(45, 226, 230, 0.60);
    }}
    #productResult:hover,
    #productResultActive:hover {{
        background: #173242;
        border-color: rgba(50, 246, 166, 0.70);
    }}
    #scannerHint {{
        background: rgba(11, 18, 25, 0.55);
        border-radius: 6px;
    }}
    #productInput,
    #productInputAccent {{
        color: #F4FAFF;
        font-size: 14px;
        padding: 0 12px;
        selection-background-color: {CYAN};
        selection-color: #061116;
    }}
    #productInput[accentText="true"],
    #productInputAccent {{
        color: {MINT};
        font-weight: 700;
    }}
    #productInput[strongText="true"] {{
        color: #F4FAFF;
        font-weight: 700;
    }}
    #brandSelectInput {{
        background: #0B141C;
        border: 1px solid rgba(45, 226, 230, 0.55);
        border-radius: 6px;
    }}
    #brandSelectLineEdit {{
        color: #F4FAFF;
        background: transparent;
        border: none;
        font-size: 14px;
        selection-background-color: {CYAN};
        selection-color: #061116;
    }}
    #productsTable #brandSelectLineEdit {{
        font-size: 13px;
        font-weight: 700;
    }}
    #brandSelectDropdown {{
        background: #0B1219;
        border: 1px solid #263948;
        border-radius: 8px;
    }}
    #brandSuggestion,
    #brandSuggestionActive,
    #brandCreateSuggestion {{
        border-bottom: 1px solid #263948;
        border-radius: 0;
    }}
    #brandSuggestion {{
        color: #DDEAF2;
        background: #0F1B24;
        font-weight: 500;
    }}
    #brandSuggestionActive {{
        color: #F4FAFF;
        background: #122632;
        font-weight: 700;
    }}
    #brandSuggestion:hover,
    #brandSuggestionActive:hover {{
        background: #173242;
    }}
    #brandCreateSuggestion {{
        color: {CYAN};
        background: #102822;
        font-weight: 700;
    }}
    #brandCreateSuggestion:hover {{
        background: #12362D;
    }}
    #brandSuggestionText {{
        color: #F4FAFF;
        font-size: 14px;
    }}
    #brandSuggestionScore,
    #brandSuggestionScoreActive {{
        color: #8FA8B9;
        font-size: 12px;
        font-weight: 700;
    }}
    #brandSuggestionScoreActive {{
        color: {MINT};
    }}
    #productSecondaryAction {{
        color: #F4FAFF;
        font-size: 13px;
        font-weight: 700;
        background: #132531;
        border: 1px solid rgba(45, 226, 230, 0.65);
        border-radius: 6px;
    }}
    #productSecondaryAction:hover {{
        background: #173242;
        border-color: rgba(50, 246, 166, 0.75);
    }}
    #primaryAction:disabled,
    #productSecondaryAction:disabled {{
        color: #6F8493;
        background: #10202A;
        border: 1px solid #263948;
    }}
    #productsTable {{
        background: #0F1B24;
        border: 1px solid #263948;
        border-radius: 4px;
        color: #DDEAF2;
        gridline-color: #263948;
        font-size: 12px;
        selection-background-color: rgba(45, 226, 230, 0.18);
        selection-color: #F4FAFF;
    }}
    #productsTable::item {{
        padding: 7px;
    }}
    #deleteRowButton {{
        background: #2A171B;
        border: 1px solid {RED};
        border-radius: 4px;
        padding: 0;
    }}
    #deleteRowButton:hover {{
        background: #3A1D22;
        border-color: #FF7A85;
    }}
    QHeaderView::section {{
        background: #0B141C;
        color: #8FA8B9;
        border: none;
        border-right: 1px solid #263948;
        border-bottom: 1px solid #263948;
        font-size: 12px;
        font-weight: 700;
        padding: 8px;
    }}
    #totalLabel {{
        color: #8FA8B9;
        font-size: 12px;
    }}
    #totalValue {{
        color: #F4FAFF;
        font-size: 12px;
        font-weight: 700;
    }}
    #totalValueAccent {{
        color: {MINT};
        font-size: 12px;
        font-weight: 700;
    }}
    #operatorText {{
        color: #DDEAF2;
        font-weight: 700;
    }}
    #sessionRoleText {{
        color: #8FA8B9;
        font-size: 12px;
        font-weight: 600;
    }}
    """
