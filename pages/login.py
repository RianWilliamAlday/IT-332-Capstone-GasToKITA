import flet as ft

CARD_GRAY = "#D9D9D9"
RED = "#A61E22"

def login_content(page: ft.Page):
    email_field = ft.TextField(
        hint_text="Enter your email",
        keyboard_type=ft.KeyboardType.EMAIL,
        border_radius=25,
        border_color="black",
        bgcolor="white",
        width=330,
        height=50,
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

    def handle_login(e):
        # Basic validation check
        if email_field.value == "attendant@fuel.com" and password_field.value == "pump123": 
            page.open(ft.SnackBar(ft.Text("Login Successful!"), bgcolor="green"))
        else:
            page.open(ft.SnackBar(ft.Text("Invalid Email or Password!"), bgcolor=RED))

    login_card = ft.Container(
        width=460,
        height=400,
        bgcolor=CARD_GRAY,
        border=ft.Border.all(2, ft.Colors.BLACK),
        border_radius=25,
        alignment=ft.Alignment(0, 0),
        padding=20,  
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            controls=[
                ft.Text(
                    "Pump Attendant Login",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Column(
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Text("Email:", size=14, weight=ft.FontWeight.BOLD),
                        email_field,
                    ],
                ),

                ft.Column(
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Text("Password:", size=14, weight=ft.FontWeight.BOLD),
                        password_field,
                    ],
                ),

                ft.Container(height=5),

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