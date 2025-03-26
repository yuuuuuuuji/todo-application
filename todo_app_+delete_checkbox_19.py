import os
import json
import PySimpleGUI as sg
import calendar
from datetime import datetime

# 保存ファイルの指定
script_dir = os.path.dirname(os.path.abspath(__file__))
todo_file = os.path.join(script_dir, "todo.json")

# ToDoリストのデフォルトデータ
todo_items = [["2025-12-31", "買い物", "牛乳を買う", False, "メモなし"]]

# 削除・移動モードのフラグ
delete_mode = False
move_mode = None  # "up" または "down"
edit_mode = False  # 編集モードのフラグ
edit_index = None  # 編集するToDoのインデックス

# 既存のデータをロード
if os.path.exists(todo_file):
    with open(todo_file, "r", encoding="utf-8") as f:
        try:
            loaded_data = json.load(f)
            if isinstance(loaded_data, list) and all(isinstance(item, list) and len(item) == 5 for item in loaded_data):
                todo_items = loaded_data
            else:
                sg.popup("保存データの形式が不正です。初期データを使用します。", title="エラー")
        except json.JSONDecodeError:
             sg.popup("保存データが壊れています。初期データを使用します。", title="エラー")

# テーブル表示用データのフォーマット
def format_table_values():
    return [[i + 1, "✔" if item[3] else "", item[1], item[2], item[0], item[4]] for i, item in enumerate(todo_items)]

# 期限が過ぎた未完了のToDoをチェックして警告色を設定
def get_row_colors():
    today = datetime.today().strftime("%Y-%m-%d")
    row_colors = []
    for i, item in enumerate(todo_items):
        deadline, completed = item[0], item[3]
        if not completed and deadline < today:  # 未完了かつ期限切れ
            row_colors.append((i, "red"))
    return row_colors

# ファイルにToDoを保存
def save_item(win):
    with open(todo_file, "w", encoding="utf-8") as f:
        json.dump(todo_items, f, ensure_ascii=False, indent=4)
    win["items"].update(values=format_table_values(), row_colors=get_row_colors())

# 並び替え処理
def sort_items(method):
    global todo_items
    if method == "期限の早い順":
        todo_items.sort(key=lambda x: x[0])
    elif method == "期限の遅い順":
        todo_items.sort(key=lambda x: x[0], reverse=True)
    elif method == "追加順":
        pass
    elif method == "古い順":
        todo_items.reverse()

# ToDoリストをカレンダーに表示するデータ形式に変換
def get_calendar_data(year, month):
    cal = calendar.Calendar(firstweekday=6)  # 日曜始まり
    month_days = cal.monthdayscalendar(year, month)

    calendar_data = []
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append("")
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                todos = [item[2] for item in todo_items if item[0] == date_str and not item[3]]  # 未完了のみ表示
                week_data.append(f"{day}\n" + "\n".join(todos) if todos else str(day))
        calendar_data.append(week_data)

    return calendar_data

# カレンダーページの表示
def show_calendar():
    today = datetime.today()
    current_date = [today.year, today.month]  # 年・月をリストで管理

    def update_calendar(win):
        win["calendar_table"].update(values=get_calendar_data(current_date[0], current_date[1]))
        win["month_label"].update(f"{current_date[0]}年 {current_date[1]}月")

    layout = [
        [sg.Button("前月", key="prev_month"), sg.Text(f"{current_date[0]}年 {current_date[1]}月", key="month_label"), sg.Button("次月", key="next_month")],
        [sg.Table(
            values=get_calendar_data(current_date[0], current_date[1]),
            headings=["日", "月", "火", "水", "木", "金", "土"],
            auto_size_columns=False,
            col_widths=[10] * 7,
            justification='center',
            key="calendar_table",
            num_rows=6,
            row_height=50
        )],
        [sg.Button("閉じる")]
    ]

    win = sg.Window("ToDoカレンダー", layout, font=("Arial", 10), resizable=True, size=(700, 400))

    while True:
        event, _ = win.read()
        if event in (sg.WIN_CLOSED, "閉じる"):
            break
        if event == "prev_month":
            if current_date[1] == 1:
                current_date[0] -= 1
                current_date[1] = 12
            else:
                current_date[1] -= 1
            update_calendar(win)
        if event == "next_month":
            if current_date[1] == 12:
                current_date[0] += 1
                current_date[1] = 1
            else:
                current_date[1] += 1
            update_calendar(win)

    win.close()

# ウィンドウ表示
def show_window():
    global todo_items, delete_mode, move_mode, edit_mode, edit_index

    sg.theme("LightBlue")

    layout = [
        [sg.Frame(title="ToDo追加", layout=[
            [sg.Text("ToDo:"), sg.Input(key="input")],
            [sg.Text("期限:"), sg.CalendarButton("期限選択", target="deadline", format="%Y-%m-%d"), sg.Input(key="deadline", visible=True, size=(12,1))],
            [sg.Text("タグ:"), sg.Combo(["買い物", "食事", "運動", "優先", "その他"], default_value="その他", key="tag", size=(10,1))],
            [sg.Text("メモ:"), sg.Input(key="memo")],
            [sg.Button("追加"), sg.Button("更新", button_color=("white", "green")), sg.Button("削除", button_color=("white", "red")), sg.Button("中止"), sg.Button("クリア")]
        ])],
        [sg.Button("並び替え:", key="sort"), sg.Combo(["期限の早い順", "期限の遅い順", "追加順", "古い順"], default_value="期限の早い順", key="sort_method", size=(15,1))],
        [sg.Button("編集", button_color=("white", "blue")), sg.Button("カレンダー")],
        [sg.Table(
            headings=["No.", "完了", "タグ", "To do", "期限", "メモ"],
            values=format_table_values(),
            col_widths=[3, 3, 10, 15, 10, 15],
            auto_size_columns=False,
            justification='left',
            row_height=30,
            alternating_row_color='#EAEAEA',
            background_color="white",
            key="items",
            enable_events=True,
            select_mode=sg.TABLE_SELECT_MODE_BROWSE,
            text_color="black",
            row_colors=get_row_colors()
        )]
    ]

    win = sg.Window("ToDoアプリ", layout, font=("Arial", 14), resizable=True, size=(900, 500))

    while True:
        event, values = win.read()
        if event == sg.WIN_CLOSED:
            break

        if event == "追加":
            if not values["deadline"]:
                sg.popup("期限を選択してください。", title="エラー")
                continue
            
            today = datetime.today().strftime("%Y-%m-%d")
            if values["deadline"] < today:
                sg.popup("過去の日付は選択できません。", title="エラー")
                win["deadline"].update("")
                continue

            new_item = [values["deadline"], values["tag"], values["input"], False, values["memo"]]
            todo_items.append(new_item)
            win["input"].update("")
            win["memo"].update("")
            win["deadline"].update("")
            save_item(win)

        if event == "更新":
            if edit_index is not None and edit_mode:
                todo_items[edit_index] = [values["deadline"], values["tag"], values["input"], False, values["memo"]]
                edit_mode = False
                edit_index = None
                win["input"].update("")
                win["memo"].update("")
                win["deadline"].update("")
                win["tag"].update("その他")
                save_item(win)
            else:
                sg.popup("編集するToDoを選択してください。", title="エラー")

        if event == "削除":
            delete_mode = True
            sg.popup("削除する行を選択してください。", title="削除モード")

        if event == "中止":
            delete_mode = False
            move_mode = None
            edit_mode = False
            edit_index = None
            sg.popup("モードを中止しました。", title="中止")
            win["input"].update("")
            win["memo"].update("")
            win["deadline"].update("")
            win["tag"].update("その他")

        if event == "クリア":
            todo_items = [item for item in todo_items if not item[3]]  # 未完了のToDoのみ残す
            save_item(win)

        if event == "sort":
            sort_method = values["sort_method"]
            sort_items(sort_method)
            save_item(win)

        if event == "編集":
            edit_mode = True
            sg.popup("行を選択してください。編集後、『更新』ボタンをクリックすることで更新されます", title="編集モード")

        if event == "カレンダー":
            show_calendar()  # カレンダーを開く

        if event == "items":  
            selected_index = values["items"]
            if selected_index:
                index = selected_index[0]

                if delete_mode:
                    if 0 <= index < len(todo_items) and todo_items[index][3]:  # チェックがついている場合のみ削除
                        del todo_items[index]
                        delete_mode = False  # 削除モードを解除
                        save_item(win)
                    else:
                        sg.popup("チェックがついていないToDoは削除できません。", title="警告")

                elif edit_mode:
                    if 0 <= index < len(todo_items):
                        edit_index = index
                        edit_values = todo_items[edit_index]
                        win["deadline"].update(edit_values[0])
                        win["tag"].update(edit_values[1])
                        win["input"].update(edit_values[2])
                        win["memo"].update(edit_values[4])
                    else:
                        sg.popup("ToDoを選択してください。", title="警告")

                else:  # チェックボックスのクリックで完了を切り替え
                    if 0 <= index < len(todo_items):
                        todo_items[index][3] = not todo_items[index][3]  # 完了状態を反転
                        save_item(win)


    win.close()

if __name__ == "__main__":
    show_window()
