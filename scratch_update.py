import re

file_path = "src/vitai/settings.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We'll locate _build_ui down to _build_config_from_ui and replace them.
# The end of _build_config_from_ui is before _get_ai_color

build_ui_code = """    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(8)

        self.tabs = QTabWidget()

        # --- TAB 1: Chung (General) ---
        self.general_tab = QWidget()
        gen_layout = QVBoxLayout(self.general_tab)
        gen_layout.setContentsMargins(12, 12, 12, 12)
        gen_layout.setSpacing(10)

        ui_language_row = QHBoxLayout()
        ui_language_row.setSpacing(12)
        self.ui_language_label = QLabel(tr("ui_language", self._config.ui_language))
        self.ui_language_label.setMinimumWidth(120)
        ui_language_row.addWidget(self.ui_language_label)
        self.ui_language_combo = QComboBox()
        for display, code in UI_LANGUAGES:
            self.ui_language_combo.addItem(display, code)
        ui_language_row.addWidget(self.ui_language_combo, 1)
        self.ui_language_combo.currentIndexChanged.connect(self._on_ui_language_changed)
        gen_layout.addLayout(ui_language_row)

        hotkey_row = QHBoxLayout()
        hotkey_row.setSpacing(12)
        self.hotkey_label = QLabel(tr("hotkey", self._config.ui_language) + " (Translate)")
        self.hotkey_label.setMinimumWidth(120)
        hotkey_row.addWidget(self.hotkey_label)
        self.modifier_combo = QComboBox()
        self.modifier_combo.setMinimumWidth(90)
        for display, code in HOTKEY_MODIFIERS:
            self.modifier_combo.addItem(display, code)
        hotkey_row.addWidget(self.modifier_combo)
        plus_label = QLabel("+")
        plus_label.setFixedWidth(16)
        plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hotkey_row.addWidget(plus_label)
        self.key_combo = QComboBox()
        self.key_combo.setMinimumWidth(60)
        for display, code in HOTKEY_KEYS:
            self.key_combo.addItem(display, code)
        self.modifier_combo.currentIndexChanged.connect(self._update_status_text)
        self.key_combo.currentIndexChanged.connect(self._update_status_text)
        hotkey_row.addWidget(self.key_combo)
        hotkey_row.addStretch()
        gen_layout.addLayout(hotkey_row)

        faa_hotkey_row = QHBoxLayout()
        faa_hotkey_row.setSpacing(12)
        self.faa_hotkey_label = QLabel("Hotkey (Ghost FAA)")
        self.faa_hotkey_label.setMinimumWidth(120)
        faa_hotkey_row.addWidget(self.faa_hotkey_label)
        self.faa_modifier_combo = QComboBox()
        self.faa_modifier_combo.setMinimumWidth(90)
        for display, code in HOTKEY_MODIFIERS:
            self.faa_modifier_combo.addItem(display, code)
        faa_hotkey_row.addWidget(self.faa_modifier_combo)
        faa_plus_label = QLabel("+")
        faa_plus_label.setFixedWidth(16)
        faa_plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        faa_hotkey_row.addWidget(faa_plus_label)
        self.faa_key_combo = QComboBox()
        self.faa_key_combo.setMinimumWidth(60)
        for display, code in HOTKEY_KEYS:
            self.faa_key_combo.addItem(display, code)
        faa_hotkey_row.addWidget(self.faa_key_combo)
        faa_hotkey_row.addStretch()
        gen_layout.addLayout(faa_hotkey_row)

        hotkey_backend_row = QHBoxLayout()
        hotkey_backend_row.setSpacing(12)
        self.hotkey_backend_label = QLabel(tr("hotkey_backend", self._config.ui_language))
        self.hotkey_backend_label.setMinimumWidth(120)
        hotkey_backend_row.addWidget(self.hotkey_backend_label)
        self.hotkey_backend_combo = QComboBox()
        for display, code in HOTKEY_BACKENDS:
            self.hotkey_backend_combo.addItem(display, code)
        hotkey_backend_row.addWidget(self.hotkey_backend_combo, 1)
        gen_layout.addLayout(hotkey_backend_row)

        self.startup_check = QCheckBox(tr("start_with_windows", self._config.ui_language))
        gen_layout.addWidget(self.startup_check)
        self.admin_check = QCheckBox(tr("run_as_admin", self._config.ui_language))
        gen_layout.addWidget(self.admin_check)
        gen_layout.addStretch()

        # --- TAB 2: Dịch thuật (Translation) ---
        self.translate_tab = QWidget()
        trans_layout = QVBoxLayout(self.translate_tab)
        trans_layout.setContentsMargins(12, 12, 12, 12)
        trans_layout.setSpacing(10)

        src_row = QHBoxLayout()
        src_row.setSpacing(12)
        self.source_label = QLabel(tr("source_language", self._config.ui_language))
        self.source_label.setMinimumWidth(120)
        src_row.addWidget(self.source_label)
        self.source_combo = QComboBox()
        for display, code in SOURCE_LANGUAGES:
            self.source_combo.addItem(display, code)
        src_row.addWidget(self.source_combo, 1)
        trans_layout.addLayout(src_row)

        tgt_row = QHBoxLayout()
        tgt_row.setSpacing(12)
        self.target_label = QLabel(tr("target_language", self._config.ui_language))
        self.target_label.setMinimumWidth(120)
        tgt_row.addWidget(self.target_label)
        self.target_combo = QComboBox()
        for display, code in TARGET_LANGUAGES:
            self.target_combo.addItem(display, code)
        tgt_row.addWidget(self.target_combo, 1)
        trans_layout.addLayout(tgt_row)

        provider_row = QHBoxLayout()
        provider_row.setSpacing(12)
        self.provider_label = QLabel(tr("translator_provider", self._config.ui_language))
        self.provider_label.setMinimumWidth(120)
        provider_row.addWidget(self.provider_label)
        self.provider_combo = QComboBox()
        for label_key, code in TRANSLATOR_PROVIDERS:
            self.provider_combo.addItem(tr(label_key, self._config.ui_language), code)
        provider_row.addWidget(self.provider_combo, 1)
        trans_layout.addLayout(provider_row)

        self.failover_check = QCheckBox(tr("translator_failover", self._config.ui_language))
        trans_layout.addWidget(self.failover_check)

        capture_row = QHBoxLayout()
        capture_row.setSpacing(12)
        self.capture_label = QLabel(tr("capture_engine", self._config.ui_language))
        self.capture_label.setMinimumWidth(120)
        capture_row.addWidget(self.capture_label)
        self.capture_combo = QComboBox()
        for display, code in CAPTURE_PROVIDERS:
            label = _availability_label(display, capture_provider_available(code), self._config.ui_language)
            self.capture_combo.addItem(label, code)
        capture_row.addWidget(self.capture_combo, 1)
        trans_layout.addLayout(capture_row)

        ocr_row = QHBoxLayout()
        ocr_row.setSpacing(12)
        self.ocr_label = QLabel(tr("ocr_engine", self._config.ui_language))
        self.ocr_label.setMinimumWidth(120)
        ocr_row.addWidget(self.ocr_label)
        self.ocr_combo = QComboBox()
        for display, code in OCR_PROVIDERS:
            label = _availability_label(display, ocr_provider_available(code), self._config.ui_language)
            self.ocr_combo.addItem(label, code)
        ocr_row.addWidget(self.ocr_combo, 1)
        trans_layout.addLayout(ocr_row)

        color_row = QHBoxLayout()
        color_row.setSpacing(12)
        self.color_label = QLabel(tr("overlay_color", self._config.ui_language))
        self.color_label.setMinimumWidth(120)
        color_row.addWidget(self.color_label)
        self.color_combo = QComboBox()
        for display, key, fill_rgba, _border in OVERLAY_COLORS:
            icon = _color_preview_icon(fill_rgba[0], fill_rgba[1], fill_rgba[2])
            self.color_combo.addItem(icon, display, key)
        color_row.addWidget(self.color_combo, 1)
        trans_layout.addLayout(color_row)

        transtyle_row = QHBoxLayout()
        transtyle_row.setSpacing(12)
        self.transtyle_label = QLabel(tr("translation_style", self._config.ui_language))
        self.transtyle_label.setMinimumWidth(120)
        transtyle_row.addWidget(self.transtyle_label)
        self.transtyle_combo = QComboBox()
        for display, profile_id in profile_choices():
            self.transtyle_combo.addItem(display, profile_id)
        transtyle_row.addWidget(self.transtyle_combo, 1)
        trans_layout.addLayout(transtyle_row)

        self.auto_check = QCheckBox(tr("auto_translate_default", self._config.ui_language))
        trans_layout.addWidget(self.auto_check)

        interval_row = QHBoxLayout()
        interval_row.setSpacing(12)
        self.interval_label = QLabel(tr("auto_interval", self._config.ui_language))
        self.interval_label.setMinimumWidth(120)
        interval_row.addWidget(self.interval_label)
        self.auto_interval_combo = QComboBox()
        for display, value in AUTO_INTERVALS:
            self.auto_interval_combo.addItem(display, value)
        interval_row.addWidget(self.auto_interval_combo, 1)
        trans_layout.addLayout(interval_row)
        
        self.transtyle_editor_btn = QPushButton(tr("edit_transtyle", self._config.ui_language))
        self.transtyle_editor_btn.clicked.connect(self._open_transtyle_editor)
        trans_layout.addWidget(self.transtyle_editor_btn)
        trans_layout.addStretch()

        # --- TAB 3: AI Assistant ---
        self.ai_tab = QWidget()
        ai_layout = QVBoxLayout(self.ai_tab)
        ai_layout.setContentsMargins(12, 12, 12, 12)
        ai_layout.setSpacing(10)

        self.ghost_faa_check = QCheckBox("Ghost FAA (Tự động AI khi bôi đen text)")
        ai_layout.addWidget(self.ghost_faa_check)
        
        self.ai_cache_check = QCheckBox("Lưu bộ nhớ tạm (nhớ đáp án đã trả lời)")
        ai_layout.addWidget(self.ai_cache_check)

        ai_provider_row = QHBoxLayout()
        ai_provider_label = QLabel("LLM Provider:")
        ai_provider_label.setMinimumWidth(100)
        ai_provider_row.addWidget(ai_provider_label)
        self.ai_provider_combo = QComboBox()
        for display, code in LLM_PROVIDERS:
            self.ai_provider_combo.addItem(display, code)
        ai_provider_row.addWidget(self.ai_provider_combo, 1)
        ai_layout.addLayout(ai_provider_row)

        ai_key_row = QHBoxLayout()
        ai_key_label = QLabel("API Key:")
        ai_key_label.setMinimumWidth(100)
        ai_key_row.addWidget(ai_key_label)
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Nhập API Key hoặc để trống dùng file .env")
        ai_key_row.addWidget(self.api_key_input, 1)
        ai_layout.addLayout(ai_key_row)

        ai_url_row = QHBoxLayout()
        ai_url_label = QLabel("Base URL:")
        ai_url_label.setMinimumWidth(100)
        ai_url_row.addWidget(ai_url_label)
        self.base_url_input = QLineEdit()
        ai_url_row.addWidget(self.base_url_input, 1)
        ai_layout.addLayout(ai_url_row)
        
        ai_model_row = QHBoxLayout()
        ai_model_label = QLabel("Model Name:")
        ai_model_label.setMinimumWidth(100)
        ai_model_row.addWidget(ai_model_label)
        self.model_input = QLineEdit()
        ai_model_row.addWidget(self.model_input, 1)
        ai_layout.addLayout(ai_model_row)

        ai_font_row = QHBoxLayout()
        ai_font_label = QLabel("Font chữ AI:")
        ai_font_label.setMinimumWidth(100)
        ai_font_row.addWidget(ai_font_label)
        self.ai_font_combo = QComboBox()
        for display, code in FONT_CHOICES:
            self.ai_font_combo.addItem(display, code)
        ai_font_row.addWidget(self.ai_font_combo, 1)
        ai_layout.addLayout(ai_font_row)

        ai_size_row = QHBoxLayout()
        ai_size_label = QLabel("Cỡ chữ AI:")
        ai_size_label.setMinimumWidth(100)
        ai_size_row.addWidget(ai_size_label)
        self.ai_size_combo = QComboBox()
        for display, code in SIZE_CHOICES:
            self.ai_size_combo.addItem(display, code)
        ai_size_row.addWidget(self.ai_size_combo, 1)
        ai_layout.addLayout(ai_size_row)

        ai_color_row = QHBoxLayout()
        ai_color_label = QLabel("Màu chữ AI:")
        ai_color_label.setMinimumWidth(100)
        ai_color_row.addWidget(ai_color_label)
        self.ai_color_combo = QComboBox()
        self.ai_color_combo.setEditable(True)
        for display, code in COLOR_CHOICES:
            self.ai_color_combo.addItem(display, code)
        ai_color_row.addWidget(self.ai_color_combo, 1)
        ai_layout.addLayout(ai_color_row)
        
        ai_layout.addStretch()

        self.tabs.addTab(self.general_tab, "⚙️ Chung")
        self.tabs.addTab(self.translate_tab, "🌐 Dịch thuật")
        self.tabs.addTab(self.ai_tab, "🤖 AI Assistant")
        content_layout.addWidget(self.tabs, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.save_btn = QPushButton(tr("save", self._config.ui_language))
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.save_btn)

        self.reset_btn = QPushButton(tr("reset", self._config.ui_language))
        self.reset_btn.setObjectName("resetButton")
        self.reset_btn.clicked.connect(self._on_reset)
        btn_row.addWidget(self.reset_btn)

        btn_row.addStretch()

        self.exit_btn = QPushButton(tr("exit", self._config.ui_language))
        self.exit_btn.setObjectName("exitButton")
        self.exit_btn.clicked.connect(self._on_exit)
        btn_row.addWidget(self.exit_btn)

        content_layout.addLayout(btn_row)

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self._update_status_text()
        content_layout.addWidget(self.status_label)

        layout.addWidget(content, 1)

    def _load_from_config(self, config: AppConfig) -> None:
        \"\"\"Populate UI controls from an AppConfig.\"\"\"
        self._set_combo_by_data(self.source_combo, config.source_language)
        self._set_combo_by_data(self.target_combo, config.target_language)
        self._set_combo_by_data(self.provider_combo, config.translator_provider)
        self.failover_check.setChecked(config.translator_failover_enabled)
        self._set_combo_by_data(self.transtyle_combo, config.default_transtyle_id)
        self._set_combo_by_data(self.color_combo, config.overlay_color)
        self._set_combo_by_data(self.ui_language_combo, config.ui_language)
        
        self._set_combo_by_data(self.modifier_combo, config.hotkey_modifier)
        self._set_combo_by_data(self.key_combo, config.hotkey_key)
        self._set_combo_by_data(self.faa_modifier_combo, config.faa_hotkey_modifier)
        self._set_combo_by_data(self.faa_key_combo, config.faa_hotkey_key)
        self._set_combo_by_data(self.hotkey_backend_combo, config.hotkey_backend)
        
        self._set_combo_by_data(self.capture_combo, config.capture_provider)
        self._set_combo_by_data(self.ocr_combo, config.ocr_provider)
        self.auto_check.setChecked(config.auto_translate_enabled)
        self._set_combo_by_data(self.auto_interval_combo, config.auto_translate_interval_ms)
        self.admin_check.setChecked(config.run_as_admin)
        self.startup_check.setChecked(config.start_with_windows)
        self.ghost_faa_check.setChecked(config.ghost_faa_enabled)
        self.ai_cache_check.setChecked(config.cache_enabled)
        self._set_combo_by_data(self.ai_provider_combo, config.provider)
        self._set_combo_by_data(self.ai_font_combo, config.font_family)
        self._set_combo_by_data(self.ai_size_combo, config.font_size)
        self.ai_color_combo.setCurrentText(config.text_color)
        
        self.api_key_input.setText(config.api_key)
        self.base_url_input.setText(config.base_url)
        self.model_input.setText(config.model)
        
        self._update_texts(config.ui_language)
        self._update_status_text()

    def _build_config_from_ui(self) -> AppConfig:
        \"\"\"Build an AppConfig from current UI state (preserving geometry from original).\"\"\"
        return AppConfig(
            x=self._config.x,
            y=self._config.y,
            width=self._config.width,
            height=self._config.height,
            target_language=str(self.target_combo.currentData()),
            source_language=str(self.source_combo.currentData()),
            translator_provider=str(self.provider_combo.currentData()),
            deepl_api_key=self._config.deepl_api_key,
            translator_failover_enabled=self.failover_check.isChecked(),
            auto_translate_enabled=self.auto_check.isChecked(),
            auto_translate_interval_ms=int(self.auto_interval_combo.currentData()),
            overlay_color=str(self.color_combo.currentData()),
            ui_language=str(self.ui_language_combo.currentData()),
            default_transtyle_id=str(self.transtyle_combo.currentData()),
            transtyle_profiles=self._config.transtyle_profiles,
            hotkey_modifier=str(self.modifier_combo.currentData()),
            hotkey_key=str(self.key_combo.currentData()),
            faa_hotkey_modifier=str(self.faa_modifier_combo.currentData()),
            faa_hotkey_key=str(self.faa_key_combo.currentData()),
            hotkey_backend=str(self.hotkey_backend_combo.currentData()),
            capture_provider=str(self.capture_combo.currentData()),
            ocr_provider=str(self.ocr_combo.currentData()),
            update_check_enabled=self._config.update_check_enabled,
            update_check_owner=self._config.update_check_owner,
            update_check_repo=self._config.update_check_repo,
            offline_translation_enabled=self._config.offline_translation_enabled,
            run_as_admin=self.admin_check.isChecked(),
            start_with_windows=self.startup_check.isChecked(),
            ghost_faa_enabled=self.ghost_faa_check.isChecked(),
            cache_enabled=self.ai_cache_check.isChecked(),
            provider=str(self.ai_provider_combo.currentData()),
            font_family=str(self.ai_font_combo.currentData()),
            font_size=int(self.ai_size_combo.currentData()),
            text_color=self._get_ai_color(),
            api_key=self.api_key_input.text().strip(),
            base_url=self.base_url_input.text().strip(),
            model=self.model_input.text().strip(),
        )
"""

start_str = "    def _build_ui(self) -> None:"
end_str = "    def _get_ai_color(self) -> str:"

start_idx = content.find(start_str)
end_idx = content.find(end_str)

new_content = content[:start_idx] + build_ui_code + "\n" + content[end_idx:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done replacing UI build and config logic.")
