from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QTextEdit, QSplitter,
    QComboBox, QFormLayout, QButtonGroup, QFileDialog, QMessageBox,
    QDialog
)
from PySide6.QtCore import Qt, Signal, QUrl, QTimer
from PySide6.QtGui import QFont, QPixmap, QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from ..engine.instrument_library import (
    LIBRARY, get_families, get_subcategories, get_by_subcategory, get_type_labels, get_tags
)
from ..engine.demakein_wrapper import HAVE_DEMAKEIN
from ..engine.instrument_icons import render_icon, render_large
from ..engine.sound_synthesizer import generate_from_note, generate_from_freq


class _ImageLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, e):
        self.clicked.emit()
        super().mousePressEvent(e)


class LibraryWidget(QWidget):
    preset_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self._net = QNetworkAccessManager(self)
        self._current_entry = None
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.7)
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._setup_ui()
        self._populate()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Instrument Library")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #D4A76A; padding: 8px 0;")
        layout.addWidget(title)

        # Family row
        fam_row = QHBoxLayout()
        fam_row.addWidget(QLabel("Family:"))
        self.fam_group = QButtonGroup(self)
        self._fam_buttons = {}
        for fam in get_families():
            btn = QPushButton(fam)
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton { padding: 6px 18px; border: 1px solid #4a4a4a; "
                "border-radius: 4px; background: #2a2a2a; color: #C0B0A0; }"
                "QPushButton:checked { background: #8B5E3C; color: #fff; border-color: #C99B5C; }"
                "QPushButton:hover:!checked { background: #3a3a3a; }"
            )
            self.fam_group.addButton(btn)
            self._fam_buttons[fam] = btn
            fam_row.addWidget(btn)
        self.fam_group.buttonClicked.connect(self._on_family_clicked)
        fam_row.addStretch()
        layout.addLayout(fam_row)

        # Subcategory combo
        sub_row = QHBoxLayout()
        sub_row.addWidget(QLabel("Type:"))
        self.sub_combo = QComboBox()
        self.sub_combo.setStyleSheet(
            "QComboBox { padding: 4px 10px; border: 1px solid #4a4a4a; border-radius: 4px; "
            "background: #2a2a2a; color: #C0B0A0; min-width: 140px; }"
            "QComboBox:hover { border-color: #C99B5C; }"
            "QComboBox::drop-down { border: none; width: 24px; }"
            "QComboBox QAbstractItemView { background: #2a2a2a; color: #C0B0A0; "
            "selection-background-color: #8B5E3C; border: 1px solid #4a4a4a; }"
        )
        self.sub_combo.currentTextChanged.connect(self._on_sub_changed)
        sub_row.addWidget(self.sub_combo)
        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet(
            "QComboBox { padding: 4px 10px; border: 1px solid #4a4a4a; border-radius: 4px; "
            "background: #2a2a2a; color: #C0B0A0; min-width: 130px; }"
            "QComboBox:hover { border-color: #C99B5C; }"
            "QComboBox::drop-down { border: none; width: 24px; }"
            "QComboBox QAbstractItemView { background: #2a2a2a; color: #C0B0A0; "
            "selection-background-color: #8B5E3C; border: 1px solid #4a4a4a; }"
        )
        self.type_combo.currentTextChanged.connect(self._filter)
        sub_row.addWidget(self.type_combo)
        sub_row.addStretch()
        layout.addLayout(sub_row)

        # Tag filter
        filter_row = QHBoxLayout()
        self.tag_filter = QComboBox()
        self.tag_filter.addItem("All Tags")
        for t in get_tags():
            self.tag_filter.addItem(t.capitalize())
        self.tag_filter.currentTextChanged.connect(self._filter)
        filter_row.addWidget(QLabel("Tag:"))
        filter_row.addWidget(self.tag_filter)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Splitter: list + detail
        splitter = QSplitter(Qt.Horizontal)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QLabel("x").sizeHint() * 3.5)
        self.list_widget.currentRowChanged.connect(self._show_detail)
        self.list_widget.setStyleSheet(
            "QListWidget { background-color: #1e1e1e; border: 1px solid #4a4a4a; border-radius: 4px; }"
            "QListWidget::item { padding: 8px; border-bottom: 1px solid #333; color: #E8D5B7; }"
            "QListWidget::item:selected { background-color: #8B5E3C; color: #fff; }"
            "QListWidget::item:hover:!selected { background-color: #3a3a3a; }"
        )
        splitter.addWidget(self.list_widget)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)

        # Image area
        self.detail_image = _ImageLabel()
        self.detail_image.setAlignment(Qt.AlignCenter)
        self.detail_image.setMinimumHeight(140)
        self.detail_image.setStyleSheet(
            "background-color: #1e1e1e; border: 1px solid #4a4a4a; border-radius: 6px; padding: 4px;"
        )
        self.detail_image.setCursor(Qt.PointingHandCursor)
        self.detail_image.clicked.connect(self._open_image)
        detail_layout.addWidget(self.detail_image)

        self.detail_name = QLabel()
        name_font = QFont()
        name_font.setPointSize(16)
        name_font.setBold(True)
        self.detail_name.setFont(name_font)
        self.detail_name.setStyleSheet("color: #E8D5B7;")
        detail_layout.addWidget(self.detail_name)

        self.detail_meta = QLabel()
        self.detail_meta.setWordWrap(True)
        self.detail_meta.setStyleSheet("color: #D4A76A; font-size: 12px; padding-bottom: 6px;")
        detail_layout.addWidget(self.detail_meta)

        self.detail_desc = QTextEdit()
        self.detail_desc.setReadOnly(True)
        self.detail_desc.setMaximumHeight(80)
        self.detail_desc.setStyleSheet("background-color: #2a2a2a; color: #C0B0A0; border: none;")
        detail_layout.addWidget(self.detail_desc)

        # Action buttons
        action_row = QHBoxLayout()
        self.download_btn = QPushButton("Download STL")
        self.download_btn.clicked.connect(self._open_download)
        self.download_btn.setEnabled(False)
        action_row.addWidget(self.download_btn)

        self.listen_btn = QPushButton("Listen")
        self.listen_btn.clicked.connect(self._open_audio)
        self.listen_btn.setEnabled(False)
        action_row.addWidget(self.listen_btn)

        self.attach_sound_btn = QPushButton("Attach Sound...")
        self.attach_sound_btn.clicked.connect(self._attach_sound)
        self.attach_sound_btn.setStyleSheet(
            "QPushButton { color: #C0B0A0; font-size: 10px; padding: 4px 8px; }"
        )
        action_row.addWidget(self.attach_sound_btn)
        action_row.addStretch()
        detail_layout.addLayout(action_row)

        # Specifications
        info_group = QGroupBox("Specifications")
        info_layout = QFormLayout(info_group)
        self.info_type = QLabel("")
        self.info_range = QLabel("")
        self.info_key = QLabel("")
        self.info_source = QLabel("")
        self.info_difficulty = QLabel("")
        info_layout.addRow("Type:", self.info_type)
        info_layout.addRow("Range:", self.info_range)
        info_layout.addRow("Key:", self.info_key)
        info_layout.addRow("Source:", self.info_source)
        info_layout.addRow("Difficulty:", self.info_difficulty)
        detail_layout.addWidget(info_group)

        self.generate_btn = QPushButton("Generate This Instrument")
        self.generate_btn.clicked.connect(self._generate)
        self.generate_btn.setEnabled(False)
        detail_layout.addWidget(self.generate_btn)

        detail_layout.addStretch()
        splitter.addWidget(detail)
        splitter.setSizes([280, 520])

        layout.addWidget(splitter, stretch=1)

        # Select first family and populate subcategories
        first = list(self._fam_buttons.keys())[0] if self._fam_buttons else None
        if first:
            self._fam_buttons[first].setChecked(True)
            self.sub_combo.addItems(get_subcategories(first))
            self._refresh_type_combo()

    def _on_family_clicked(self, button):
        family = button.text()
        self.sub_combo.blockSignals(True)
        self.sub_combo.clear()
        self.sub_combo.addItems(get_subcategories(family))
        self.sub_combo.blockSignals(False)
        self._refresh_type_combo()
        self._populate()

    def _current_family(self):
        for fam, btn in self._fam_buttons.items():
            if btn.isChecked():
                return fam
        return ""

    def _current_subcategory(self):
        return self.sub_combo.currentText()

    def _populate(self):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        family = self._current_family()
        sub = self._current_subcategory()
        type_label = self.type_combo.currentText()
        tag = self.tag_filter.currentText().lower()

        entries = get_by_subcategory(family, sub) if family and sub else LIBRARY
        for entry in entries:
            if type_label and type_label != "All Types" and entry.type_label != type_label:
                continue
            if tag != "all tags" and tag not in entry.tags:
                continue
            item = QListWidgetItem()
            icon = render_icon(entry.type_label, 48, 32)
            item.setIcon(icon)
            item.setText(entry.name)
            item.setData(Qt.UserRole + 1, entry.name)
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_sub_changed(self, sub):
        self._refresh_type_combo()
        self._populate()

    def _refresh_type_combo(self):
        family = self._current_family()
        sub = self._current_subcategory()
        self.type_combo.blockSignals(True)
        self.type_combo.clear()
        labels = get_type_labels(family, sub)
        if len(labels) > 1:
            self.type_combo.addItem("All Types")
            self.type_combo.addItems(labels)
            self.type_combo.show()
        else:
            self.type_combo.hide()
        self.type_combo.blockSignals(False)

    def _filter(self):
        self._populate()

    def _show_detail(self, row):
        if row < 0:
            return
        item = self.list_widget.item(row)
        if not item:
            return
        name = item.data(Qt.UserRole + 1)
        entry = next((e for e in LIBRARY if e.name == name), None)
        if not entry:
            return

        # Show SVG large preview
        pix = render_large(entry.type_label, 280, 160)
        self.detail_image.setPixmap(pix)
        self.detail_image.setToolTip("Click to view photo" if entry.image_url else "")

        self.detail_name.setText(entry.name)
        self.detail_meta.setText(f"{entry.type_label}  |  {entry.range}  |  Key of {entry.key}")
        self.detail_desc.setText(entry.description)
        self.info_type.setText(entry.type_label)
        self.info_range.setText(entry.range)
        self.info_key.setText(entry.key)
        self.info_source.setText(entry.source)
        self.info_difficulty.setText(entry.difficulty)
        self.generate_btn.setEnabled(bool(entry.demakein_preset) and HAVE_DEMAKEIN)
        self.download_btn.setEnabled(bool(entry.download_url))
        can_listen = bool(entry.audio_url) or bool(entry.demakein_preset)
        self.listen_btn.setEnabled(can_listen)
        self._current_entry = entry

        # Try to load web image for the detail view
        if entry.image_url:
            self._load_web_image(entry.image_url)

    def _load_web_image(self, url):
        from PySide6.QtCore import QByteArray
        req = QNetworkRequest(QUrl(url))
        req.setTransferTimeout(8000)
        reply = self._net.get(req)
        reply.finished.connect(lambda r=reply: self._on_image_loaded(r))

    def _on_image_loaded(self, reply):
        if reply.error() == 0:
            data = reply.readAll()
            pix = QPixmap()
            if pix.loadFromData(data):
                pix = pix.scaled(280, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.detail_image.setPixmap(pix)

    def _open_image(self):
        if self._current_entry and self._current_entry.image_url:
            QDesktopServices.openUrl(QUrl(self._current_entry.image_url))

    def _open_download(self):
        if self._current_entry and self._current_entry.download_url:
            QDesktopServices.openUrl(QUrl(self._current_entry.download_url))

    def _open_audio(self):
        if not self._current_entry:
            return
        entry = self._current_entry
        if entry.audio_url:
            QDesktopServices.openUrl(QUrl(entry.audio_url))
            return
        if entry.demakein_preset:
            self._play_synthesized(entry)

    def _play_synthesized(self, entry):
        range_map = {"Soprano": 5, "Alto": 4, "Tenor": 3, "Bass": 2, "Contrabass": 1}
        octave = range_map.get(entry.range, 4)
        note = entry.key.rstrip("b#") + str(octave)
        type_map = {"flute": "flute", "fipple": "flute", "reed": "reed",
                    "single reed": "reed", "double reed": "reed",
                    "brass": "brass", "brasswind": "brass"}
        inst_type = "flute"
        for k, v in type_map.items():
            if k in entry.type_label.lower():
                inst_type = v
                break
        path = generate_from_note(note, inst_type)
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()
        self.listen_btn.setText("Playing...")
        self.listen_btn.setEnabled(False)

    def _on_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.listen_btn.setText("Listen")
            self.listen_btn.setEnabled(True)

    def _attach_sound(self):
        if not self._current_entry:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Attach Sound File", "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a);;All Files (*.*)"
        )
        if path:
            self._current_entry.audio_url = path
            self.listen_btn.setEnabled(True)
            self.listen_btn.setText("Play Local")

    def _generate(self):
        if hasattr(self, '_current_entry') and self._current_entry:
            self.preset_selected.emit(self._current_entry.demakein_preset)
