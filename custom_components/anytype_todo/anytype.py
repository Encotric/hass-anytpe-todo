"Anytype markdown parsing and rendering logic, as well as the AnytypeMarkdownToDoPage class which represents a parsed markdown page with to-do lists."

import marko
from homeassistant.components.todo import (
    TodoItem,
)
from homeassistant.components.todo.const import TodoItemStatus
from homeassistant.exceptions import HomeAssistantError
from marko.block import Document, List, ListItem
from marko.inline import InlineElement
from marko.md_renderer import MarkdownRenderer


class ToDoListItemMarkdown(InlineElement):
    pattern = r"\[([ xX])\]\s+(.*)"
    parse_children = False

    def __init__(self, match):
        self.completed = match.group(1) != " "
        self.summary = match.group(2)


class TodoListItemMarkdownRenderer(object):
    def render_to_do_list_item_markdown(self, element: ToDoListItemMarkdown):
        return f"[{'x' if element.completed else ' '}] {element.summary}"


todo_extension = marko.MarkoExtension(
    elements=[ToDoListItemMarkdown], renderer_mixins=[TodoListItemMarkdownRenderer]
)


class AnytypeMarkdownTodoItem:
    summary: str
    completed: bool
    uid: str

    def __init__(self, *, summary: str, completed: bool, idx: int):
        self.summary = summary
        self.completed = completed
        self.uid = str(hash((summary, completed, idx)))

    def convert_to_hass(self) -> TodoItem:
        return TodoItem(
            uid=self.uid,
            summary=self.summary,
            status=TodoItemStatus.COMPLETED
            if self.completed
            else TodoItemStatus.NEEDS_ACTION,
            description=None,
        )


class AnytypeMarkdownTodoList:
    name: str
    ast_index: int
    items: list[AnytypeMarkdownTodoItem]
    length: int

    def __init__(self, name: str, ast_index: int, items: list[AnytypeMarkdownTodoItem]):
        self.name = name
        self.ast_index = ast_index
        self.items = items
        self.length = len(items)

    def __len__(self):
        return self.length

    def get_item(self, uid: str) -> AnytypeMarkdownTodoItem | None:
        for item in self.items:
            if item.uid == uid:
                return item

        return None

    def remove_item(self, uid: str):
        item = self.get_item(uid)
        if item is None:
            raise HomeAssistantError("Anytype API: tried to remove non-existing item.")
        self.items.remove(item)
        self.length -= 1

    def update_item(
        self,
        uid: str,
        *,
        summary: str | None = None,
        completed: bool | None = None,
    ) -> None:
        """Update an item in place and keep its generated UID in sync."""
        item = self.get_item(uid)
        if item is None:
            raise HomeAssistantError("Anytype API: tried to update non-existing item.")

        idx = self.items.index(item)
        if summary is not None:
            item.summary = summary
        if completed is not None:
            item.completed = completed
        item.uid = str(hash((item.summary, item.completed, idx)))

    def add_item(self, item: AnytypeMarkdownTodoItem):
        self.items.append(item)
        self.length += 1

    def to_markdown(self) -> str:
        result = str()
        for item in self.items:
            result += f"- [{'x' if item.completed else ' '}] {item.summary}\n"

        result += "- [ ] \n"
        return result


marko_instance = marko.Markdown(extensions=[todo_extension], renderer=MarkdownRenderer)


class AnytypeMarkdownToDoPage:
    lists: list[AnytypeMarkdownTodoList]
    ast: Document

    def __init__(self, markdown: str) -> None:
        self.ast = marko_instance.parse(markdown)
        self.lists = []

        current_list_name: str | None = None
        current_list_index: int | None = None
        current_list_items: list[AnytypeMarkdownTodoItem] = []

        for i, child in enumerate(self.ast.children):
            if child.get_type(snake_case=True) == "heading":
                heading = child.children[0]
                if (
                    heading.get_type(snake_case=True) == "emphasis"
                    or heading.get_type(snake_case=True) == "strong_emphasis"
                ):
                    heading = heading.children[0]

                list_title = heading.children
                if current_list_name is not None and current_list_index is not None:
                    self.lists.append(
                        AnytypeMarkdownTodoList(
                            name=current_list_name,
                            ast_index=current_list_index,
                            items=current_list_items,
                        )
                    )
                    current_list_items = []

                current_list_name = list_title
            if child.get_type(snake_case=True) == "list":
                current_list_index = i
                for idx, item in enumerate(child.children):
                    paragraph = item.children[0]
                    todo_item = paragraph.children[0]
                    summary = todo_item.summary.strip()
                    completed = todo_item.completed
                    if summary != "":
                        current_list_items.append(
                            AnytypeMarkdownTodoItem(
                                summary=summary, completed=completed, idx=idx
                            )
                        )

        if current_list_name is not None and current_list_index is not None:
            self.lists.append(
                AnytypeMarkdownTodoList(
                    name=current_list_name,
                    ast_index=current_list_index,
                    items=current_list_items,
                )
            )

    def get_list(self, name: str) -> AnytypeMarkdownTodoList | None:
        for todo_list in self.lists:
            if todo_list.name == name:
                return todo_list
        return None

    def to_markdown(self) -> str:
        result = ""
        last_ast_index = 0
        for todo_list in self.lists:
            doc = Document()
            doc.children = self.ast.children[last_ast_index : todo_list.ast_index]
            result += marko_instance.render(doc)
            result += todo_list.to_markdown()
            last_ast_index = todo_list.ast_index + 1

        if len(self.ast.children) - 1 > last_ast_index:
            doc = Document()
            doc.children = self.ast.children[last_ast_index:]
            result += marko_instance.render(doc)

        return result
