import flet as ft


def main(page: ft.Page):
    page.title = "U-FUEL"
    page.bgcolor = "#8B0000"
    page.padding = 0
    page.window.width = 360
    page.window.height = 700

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Image(
                        src="assets/u-fuel_logo.jpg",
                        width=55,
                        height=55,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                    bgcolor="#FFFFF",
                    border_radius=8,
                    padding=ft.Padding.all(6),
                    width=55,
                    height=55,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Text(
                    "U-FUEL",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color="white",
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
    )

    email_field = ft.TextField(
        label="EMAIL ADDRESS",
        label_style=ft.TextStyle(
            size=11,
            weight=ft.FontWeight.BOLD,
            color="#555555",
        ),
        filled=True,
        fill_color="#EBEBEB",
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#8B0000",
        border_radius=10,
        text_style=ft.TextStyle(size=14),
    )

    password_field = ft.TextField(
        label="PASSWORD",
        label_style=ft.TextStyle(
            size=11,
            weight=ft.FontWeight.BOLD,
            color="#555555",
        ),
        password=True,
        can_reveal_password=True,
        filled=True,
        fill_color="#EBEBEB",
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#8B0000",
        border_radius=10,
        text_style=ft.TextStyle(size=14),
    )

    login_button = ft.Button(
        content="LOGIN",
        bgcolor="#8B0000",
        color="white",
        width=float("inf"),
        height=50,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            text_style=ft.TextStyle(
                size=15,
                weight=ft.FontWeight.BOLD,
                letter_spacing=1.5,
            ),
        ),
    )

    login_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "LOGIN",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color="#111111",
                ),
                ft.Container(height=24),
                email_field,
                ft.Container(height=14),
                password_field,
                ft.Container(height=28),
                login_button,
            ],
            spacing=0,
            scroll=ft.ScrollMode.ADAPTIVE,
        ),
        bgcolor="white",
        border_radius=ft.BorderRadius(
            top_left=28,
            top_right=28,
            bottom_left=0,
            bottom_right=0,
        ),
        padding=ft.Padding.symmetric(horizontal=24, vertical=36),
        expand=True,
    )

    footer = ft.Container(
        content=ft.Text(
            "GAStoKITA",
            size=13,
            color="white",
            text_align=ft.TextAlign.CENTER,
        ),
        bgcolor="#8B0000",
        padding=ft.Padding.symmetric(vertical=14),
        alignment=ft.Alignment.CENTER,
    )

    page.add(
        ft.Column(
            controls=[
                header,
                ft.Container(height=10),
                login_card,
                footer,
            ],
            expand=True,
            spacing=0,
        )
    )


ft.run(main)