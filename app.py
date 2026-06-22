import flet as ft
from flet import Colors

def main(page: ft.Page):
    page.title = "GasToKita"
    
    # 1. Theme and Color Adjustments
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = Colors.WHITE 
    page.padding = 40  
    page.window.full_screen = False  
    page.window.maximized = True
    page.update()

    header = ft.Column([
    ft.Text("GasToKita", size=36, weight=ft.FontWeight.BOLD, color=Colors.BLUE_500),
        ft.Divider(height=30, color=Colors.BLACK)
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