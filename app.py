import flet as ft
from flet import Colors

def main(page: ft.Page):
    page.title = "GasToKita"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = Colors.WHITE 
    page.padding = 40  
    page.window.full_screen = False  
    page.window.maximized = True
    page.update()

    header = ft.Column([
        ft.Container(
            content=ft.Text(
                "GasToKita", 
                size=36, 
                weight=ft.FontWeight.BOLD, 
                color=Colors.WHITE
            ),
            bgcolor="#9F2323", 
            alignment=ft.Alignment(0, 0), 
            padding=20,                          
            border_radius=8,                     
        ),
    ])

    page.add(
        ft.Column([
            header,
            ft.Container(height=30)
        ], 
        expand=True, 
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        )
    )

ft.run(main)