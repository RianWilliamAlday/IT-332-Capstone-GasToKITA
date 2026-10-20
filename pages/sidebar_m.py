
import asyncio
import flet as ft

MOBILE_RED = "#8B0000"
SIDEBAR_W = 270
HIDDEN_LEFT = -(SIDEBAR_W + 30)
SLIDE_MS = 250

MENU_ITEMS = [
    ("pos", ft.Icons.POINT_OF_SALE, "POS"),
    ("history", ft.Icons.HISTORY, "History"),
]

class Sidebar:
    def __init__(self, page: ft.Page, auth: dict, active: str = "pos"):
        self.page = page
        self.auth = auth
        self.active = active
        self._open = False

        anim = ft.Animation(SLIDE_MS, ft.AnimationCurve.EASE_OUT)

        self.scrim = ft.Container(
            visible=False, opacity=0, animate_opacity=anim,
            left=0, top=0, right=0, bottom=0,
            bgcolor="#80000000", on_click=self.close,
        )
        self.panel = ft.Container(
            left=HIDDEN_LEFT, top=0, bottom=0, width=SIDEBAR_W,
            animate_position=anim,
            bgcolor="white",
            shadow=ft.BoxShadow(blur_radius=16, color="#55000000", offset=ft.Offset(4, 0)),
            content=self._build_panel(),
        )

    def menu_button(self, color: str = "white", size: int = 26) -> ft.IconButton:
        return ft.IconButton(icon=ft.Icons.MENU, icon_color=color, icon_size=size, on_click=self.open)

    def wrap(self, main_content: ft.Control) -> ft.Stack:
        return ft.Stack(expand=True, controls=[main_content, self.scrim, self.panel])

    async def open(self, e=None):
        self._open = True
        self.scrim.visible = True
        self.page.update()
        await asyncio.sleep(0.03)
        self.panel.left = 0
        self.page.update()

    async def close(self, e=None):
        self._open = False
        self.scrim.opacity = 0
        self.panel.left = HIDDEN_LEFT
        self.page.update()
        await asyncio.sleep(SLIDE_MS / 1000)
        if not self._open: 
            self.scrim.visible = False
            self.page.update()

    def _menu_item(self, icon, label, on_click, active=False):
        color = MOBILE_RED if active else "#333333"
        return ft.Container(
            content=ft.Row(spacing=16, controls=[
                ft.Icon(icon, size=22, color=color),
                ft.Text(label, size=15, color=color, weight=ft.FontWeight.BOLD if active else ft.FontWeight.W_500),
            ]),
            bgcolor="#FDECEC" if active else None,
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=16, vertical=14),
            ink=True, on_click=on_click,
        )

    def _build_panel(self):
        header = ft.Container(
            bgcolor=MOBILE_RED, padding=ft.Padding.symmetric(horizontal=20, vertical=20),
            content=ft.Row(spacing=12, controls=[
                ft.Container(content=ft.Image(src="u-fuel_logo.jpg", width=40, height=40, fit=ft.BoxFit.CONTAIN),
                             bgcolor="white", border_radius=8, padding=4, width=48, height=48),
                ft.Column(spacing=0, controls=[
                    ft.Text("U-FUEL", size=16, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("Pump Attendant", size=12, color="white"),
                ]),
            ]),
        )
        items = []
        for key, icon, label in MENU_ITEMS:
            is_active = key == self.active
            handler = self.close if is_active else (lambda e, k=key: self._open_page(k))
            items.append(self._menu_item(icon, label, handler, active=is_active))

        return ft.Column(spacing=0, controls=[
            header,
            ft.Container(padding=ft.Padding.symmetric(horizontal=12, vertical=12), content=ft.Column(spacing=4, controls=items)),
            ft.Container(expand=True),
            ft.Divider(height=1, color="#E6E6E6"),
            ft.Container(padding=ft.Padding.symmetric(horizontal=12, vertical=12),
                         content=self._menu_item(ft.Icons.LOGOUT, "Logout", self._logout)),
        ])

    def _open_page(self, key: str):
        page, auth = self.page, self.auth
        if key == "pos":
            from pages.select_pa_m import build_pa_page_mobile as builder
        elif key == "history":
            from pages.c_history_m import build_history_page_mobile as builder
        else:
            return
        page.controls.clear()
        page.add(builder(page, auth))
        page.update()

    async def _logout(self, e):
        page, auth = self.page, self.auth
        for key in ("gastokita.auth_token", "gastokita.user_json"):
            try:
                await page.shared_preferences.remove(key)
            except Exception as ex:
                print(f"[sidebar] failed to remove {key}: {ex}")

        auth.clear()
        auth.update({"token": None, "role": None, "user": None})
        page.controls.clear()
        from mobile_app import show_login
        page.add(show_login(page, auth))
        page.update()