import flet as ft

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"

def admin(page: ft.Page):
    page.title = "GasToKITA"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = LIGHT_GRAY
    page.padding = 0
    page.window.maximized = True

    header = ft.Container(
        bgcolor=RED,
        height=100,
        padding=20,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "GAStoKITA",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color="white",
                ),

                ft.Row(
                    spacing=15,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "U-Fuel",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color="white",
                        ),

                        ft.Container(
                            width=70,
                            height=70,
                            bgcolor="white",
                            border_radius=12,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Image(
                                src="u-fuel_logo.jpg",
                                fit=ft.BoxFit.CONTAIN,
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )

    footer = ft.Container(
        height=80,
        bgcolor=RED,
    )

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
                        password_field
                    ],
                ),
                ft.Button(
                    "Login",
                    width=130,
                    height=45,
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
    

    page.add(
        ft.Column(
            spacing=0,
            expand=True,
            controls=[
                header,

                ft.Container(
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                    content=login_card,
                ),

                footer,
            ],
        )
    )

ft.run(admin)