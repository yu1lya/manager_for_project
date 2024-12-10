import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLineEdit, QComboBox, QDialog, QFormLayout,
    QTableWidget, QTableWidgetItem, QDateEdit, QCheckBox, QTabWidget, QTextEdit, QGroupBox, QHBoxLayout
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QIcon


class EditProjectDialog(QDialog):
    def __init__(self, project=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование проекта")
        self.setFixedSize(400, 300)

        self.layout = QFormLayout(self)

        self.name_input = QLineEdit(self)
        self.url_input = QLineEdit(self)
        self.status_input = QComboBox(self)
        self.status_input.addItems(["Не начат", "В процессе", "Завершен"])
        self.date_input = QDateEdit(self)
        self.date_input.setDate(QDate.currentDate())
        self.favorite_input = QCheckBox("Избранное", self)
        self.description_input = QTextEdit(self)
        self.priority_input = QComboBox(self)
        self.priority_input.addItems(["Низкий", "Средний", "Высокий"])  # Добавляем варианты приоритета

        if project:
            self.name_input.setText(project["name"])
            self.url_input.setText(project["url"])
            self.status_input.setCurrentText(project["status"])
            self.date_input.setDate(QDate.fromString(project["date"], 'yyyy-MM-dd'))
            self.favorite_input.setChecked(project["is_favorite"])
            self.description_input.setText(project["description"])
            self.priority_input.setCurrentText(project["priority"])  # Устанавливаем выбранный приоритет

        # Группируем поля ввода
        input_group = QGroupBox("Информация о проекте")
        input_layout = QFormLayout()
        input_layout.addRow("Название:", self.name_input)
        input_layout.addRow("Краткое описание:", self.description_input)
        input_layout.addRow("Ссылка:", self.url_input)
        input_layout.addRow("Статус:", self.status_input)
        input_layout.addRow("Дата защиты:", self.date_input)
        input_layout.addRow("Приоритет:", self.priority_input)  # Поле для приоритета
        input_layout.addRow(self.favorite_input)
        input_group.setLayout(input_layout)

        self.layout.addWidget(input_group)

        self.save_button = QPushButton("Сохранить", self)
        self.save_button.setIcon(QIcon("save_icon.png"))  # Добавьте иконку для кнопки
        self.save_button.clicked.connect(self.save_project)
        self.layout.addRow(self.save_button)

        self.setLayout(self.layout)

    def save_project(self):
        self.accept()

    def get_project_data(self):
        return {
            "name": self.name_input.text(),
            "url": self.url_input.text(),
            "status": self.status_input.currentText(),
            "date": self.date_input.date().toString('yyyy-MM-dd'),
            "is_favorite": self.favorite_input.isChecked(),
            "description": self.description_input.toPlainText(),
            "priority": self.priority_input.currentText()  # Возвращаем выбранный приоритет
        }


class ProjectManager(QWidget):

    def create_database(self):
        self.conn = sqlite3.connect("projects.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            url TEXT NOT NULL,
            date TEXT NOT NULL,
            is_favorite INTEGER NOT NULL DEFAULT 0,
            description TEXT NOT NULL DEFAULT '',
            priority TEXT NOT NULL DEFAULT 'Низкий'  -- Добавляем поле для приоритета
        )
        ''')
        self.conn.commit()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Менеджер проектов")
        self.setGeometry(100, 100, 800, 600)

        self.create_database()
        self.initUI()
        self.load_data()

    def initUI(self):
        self.layout = QVBoxLayout()

        # Поле для поиска
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Поиск по имени проекта...")
        self.search_input.textChanged.connect(self.search_projects)  # Подключаем к методу поиска
        self.layout.addWidget(self.search_input)

        self.tabs = QTabWidget(self)
        self.layout.addWidget(self.tabs)

        # Вкладка для всех проектов
        self.all_projects_tab = QWidget()
        self.all_projects_layout = QVBoxLayout()
        self.all_projects_tab.setLayout(self.all_projects_layout)

        self.all_projects_table = QTableWidget(self)
        self.all_projects_table.setColumnCount(7)
        self.all_projects_table.setHorizontalHeaderLabels(
            ["Название", "Краткое описание", "Статус", "Ссылка", "Дата защиты", "Приоритет", "Избранное"])
        self.all_projects_layout.addWidget(self.all_projects_table)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Добавить проект", self)
        self.add_button.setIcon(QIcon("add_icon.png"))
        self.add_button.clicked.connect(self.add_project)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Редактировать проект", self)
        self.edit_button.setIcon(QIcon("edit_icon.png"))
        self.edit_button.clicked.connect(self.edit_project)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Удалить проект", self)
        self.delete_button.setIcon(QIcon("delete_icon.png"))
        self.delete_button.clicked.connect(self.delete_project)
        button_layout.addWidget(self.delete_button)

        self.all_projects_layout.addLayout(button_layout)

        self.tabs.addTab(self.all_projects_tab, "Все проекты")

        # Вкладка для избранных проектов
        self.favorite_projects_tab = QWidget()
        self.favorite_projects_layout = QVBoxLayout()
        self.favorite_projects_tab.setLayout(self.favorite_projects_layout)

        self.favorite_projects_table = QTableWidget(self)
        self.favorite_projects_table.setColumnCount(6)
        self.favorite_projects_table.setHorizontalHeaderLabels(
            ["Название", "Краткое описание", "Статус", "Ссылка", "Дата защиты", "Приоритет"])
        self.favorite_projects_layout.addWidget(self.favorite_projects_table)

        self.tabs.addTab(self.favorite_projects_tab, "Избранное")

        self.setLayout(self.layout)

    def search_projects(self):
        search_text = self.search_input.text().lower()  # Получаем текст поиска и приводим к нижнему регистру
        self.update_all_projects_table(search_text)  # Передаем текст поиска в метод обновления таблицы

    def update_all_projects_table(self, search_text=""):
        self.all_projects_table.setRowCount(0)
        self.cursor.execute('SELECT * FROM projects')
        for row in self.cursor.fetchall():
            if search_text in row[1].lower():  # Проверяем, содержится ли текст поиска в названии проекта
                row_position = self.all_projects_table.rowCount()
                self.all_projects_table.insertRow(row_position)
                self.all_projects_table.setItem(row_position, 0, QTableWidgetItem(row[1]))
                self.all_projects_table.setItem(row_position, 1, QTableWidgetItem(row[6]))
                self.all_projects_table.setItem(row_position, 2, QTableWidgetItem(row[2]))
                self.all_projects_table.setItem(row_position, 3, QTableWidgetItem(row[3]))
                self.all_projects_table.setItem(row_position, 4, QTableWidgetItem(row[4]))
                self.all_projects_table.setItem(row_position, 5, QTableWidgetItem(row[7]))

                star_button = QPushButton("★" if row[5] else "☆", self)
                star_button.setCheckable(True)
                star_button.setChecked(bool(row[5]))
                star_button.clicked.connect(
                    lambda checked, project_id=row[0]: self.toggle_favorite(checked, project_id))
                self.all_projects_table.setCellWidget(row_position, 6, star_button)


    def add_project(self):
        dialog = EditProjectDialog(parent=self)
        if dialog.exec():
            project_data = dialog.get_project_data()
            self.cursor.execute('INSERT INTO projects (name, status, url, date, is_favorite, description, priority) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                (project_data["name"], project_data["status"], project_data["url"], project_data["date"], project_data["is_favorite"], project_data["description"], project_data["priority"]))
            self.conn.commit()
            self.update_project_tables()

    def edit_project(self):
        current_row = self.all_projects_table.currentRow()
        if current_row >= 0:
            project_name = self.all_projects_table.item(current_row, 0).text()
            project_description = self.all_projects_table.item(current_row, 1).text()
            project_status = self.all_projects_table.item(current_row, 2).text()
            project_url = self.all_projects_table.item(current_row, 3).text()
            project_date = self.all_projects_table.item(current_row, 4).text()
            project_priority = self.all_projects_table.item(current_row, 5).text()  # Получаем приоритет
            project_id = self.cursor.execute('SELECT id FROM projects WHERE name=? AND status=? AND url=? AND date=? AND description=? AND priority=?',
                                              (project_name, project_status, project_url, project_date, project_description, project_priority)).fetchone()[0]
            project = self.cursor.execute('SELECT * FROM projects WHERE id=?', (project_id,)).fetchone()
            dialog = EditProjectDialog({
                "id": project[0],
                "name": project[1],
                "status": project[2],
                "url": project[3],
                "date": project[4],
                "is_favorite": bool(project[5]),
                "description": project[6],
                "priority": project[7]  # Передаем приоритет в диалог
            }, self)
            if dialog.exec():
                updated_data = dialog.get_project_data()
                self.cursor.execute('UPDATE projects SET name=?, status=?, url=?, date=?, is_favorite=?, description=?, priority=? WHERE id=?',
                                    (updated_data["name"], updated_data["status"], updated_data["url"], updated_data["date"], updated_data["is_favorite"], updated_data["description"], updated_data["priority"], project_id))
                self.conn.commit()
                self.update_project_tables()

    def delete_project(self):
        current_row = self.all_projects_table.currentRow()
        if current_row >= 0:
            project_name = self.all_projects_table.item(current_row, 0).text()
            project_description = self.all_projects_table.item(current_row, 1).text()
            project_status = self.all_projects_table.item(current_row, 2).text()
            project_url = self.all_projects_table.item(current_row, 3).text()
            project_date = self.all_projects_table.item(current_row, 4).text()
            project_priority = self.all_projects_table.item(current_row, 5).text()  # Получаем приоритет
            project_id = self.cursor.execute('SELECT id FROM projects WHERE name=? AND status=? AND url=? AND date=? AND description=? AND priority=?',
                                              (project_name, project_status, project_url, project_date, project_description, project_priority)).fetchone()[0]
            self.cursor.execute('DELETE FROM projects WHERE id=?', (project_id,))
            self.conn.commit()
            self.update_project_tables()

    def update_project_tables(self):
        self.update_all_projects_table()
        self.update_favorite_projects_table()

    def toggle_favorite(self, checked, project_id):
        self.cursor.execute('UPDATE projects SET is_favorite=? WHERE id=?', (1 if checked else 0, project_id))
        self.conn.commit()
        self.update_project_tables()

    def update_favorite_projects_table(self):
        self.favorite_projects_table.setRowCount(0)
        self.cursor.execute('SELECT * FROM projects WHERE is_favorite=1')
        for row in self.cursor.fetchall():
            row_position = self.favorite_projects_table.rowCount()
            self.favorite_projects_table.insertRow(row_position)
            self.favorite_projects_table.setItem(row_position, 0, QTableWidgetItem(row[1]))
            self.favorite_projects_table.setItem(row_position, 1, QTableWidgetItem(row[6]))
            self.favorite_projects_table.setItem(row_position, 2, QTableWidgetItem(row[2]))
            self.favorite_projects_table.setItem(row_position, 3, QTableWidgetItem(row[3]))
            self.favorite_projects_table.setItem(row_position, 4, QTableWidgetItem(row[4]))
            self.favorite_projects_table.setItem(row_position, 5, QTableWidgetItem(row[7]))  # Устанавливаем приоритет

    def load_data(self):
        self.update_project_tables()

    def closeEvent(self, event):
        self.conn.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    manager = ProjectManager()
    manager.show()
    sys.exit(app.exec())
