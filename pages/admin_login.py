import flet as ft

CARD_GRAY = "#D9D9D9"
RED = "#A61E22"

def login_content(page: ft.Page):
    password_field = ft.TextField(
        hint_text="Enter your password",
        password=True,
        can_reveal_password=True,
        border_radius=25,
        border_color="black",
        bgcolor="white",
        width=330,
        height=50,
    )

    def handle_login(e):
        if password_field.value == "admin123": 
            page.navigate("/dashboard")
        else:
            page.open(ft.SnackBar(ft.Text("Incorrect Password!"), bgcolor=RED))


    login_card = ft.Container(
        width=460,
        height=320,
        bgcolor=CARD_GRAY,
        border=ft.Border.all(2, ft.Colors.BLACK),
        border_radius=25,
        alignment=ft.Alignment(0, 0),
        padding=20,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=18,
            controls=[
                ft.Text(
                    "Admin Login",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Please enter your password to enter the admin system",
                    size=14,
                    weight=ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Column(
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Text(
                            "Password:",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        password_field,
                    ],
                ),
                ft.ElevatedButton(
                    "Login",
                    width=130,
                    height=45,
                    on_click=handle_login,
                    style=ft.ButtonStyle(
                        bgcolor=RED,
                        color="white",
                        shape=ft.RoundedRectangleBorder(radius=25),
                        text_style=ft.TextStyle(
                            size=20,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ),
                ),
            ],
        ),
    )

    return ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        content=login_card,
    )
