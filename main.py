import threading
import flet as ft
import flet_audio as fta
import yt_dlp


def main(page: ft.Page):
    page.title = "YT Music Android"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#030303"
    page.padding = 15

    # Инициализация аудиоплеера для Android / Desktop
    audio_player = fta.Audio(
        src="https://github.com/mdn/webaudio-examples/blob/main/audio-basics/outfoxing.mp3?raw=true",
        autoplay=False,
    )
    page.overlay.append(audio_player)

    is_playing = False

    # Элементы интерфейса
    status_text = ft.Text(
        "Выберите трек",
        size=14,
        weight=ft.FontWeight.BOLD,
        color="white",
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS,
    )
    results_list = ft.ListView(expand=True, spacing=8)
    search_input = ft.TextField(
        hint_text="Поиск песен или артистов...",
        expand=True,
        bgcolor="#1a1a1a",
        border_radius=8,
        border_color="transparent",
        on_submit=lambda e: search_music(e),
    )

    def search_music(e):
        query = search_input.value.strip()
        if not query:
            return
        status_text.value = "⏳ Поиск треков..."
        results_list.controls.clear()
        page.update()
        threading.Thread(
            target=fetch_results, args=(query,), daemon=True
        ).start()

    def fetch_results(query):
        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "extract_flat": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch15:{query}", download=False)
                tracks = info.get("entries", [])

            results_list.controls.clear()
            for t in tracks:
                title = t.get("title", "Без названия")
                url = (
                    t.get("url")
                    or f"https://www.youtube.com/watch?v={t.get('id')}"
                )
                duration = t.get("duration")
                dur_str = (
                    f"{int(duration // 60)}:{int(duration % 60):02d}"
                    if duration
                    else ""
                )

                results_list.controls.append(
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(
                                ft.Icons.MUSIC_NOTE, color="#ff0000"
                            ),
                            title=ft.Text(
                                title,
                                color="white",
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            trailing=ft.Text(dur_str, color="grey", size=12),
                            on_click=lambda e, u=url, ti=title: play_track(
                                u, ti
                            ),
                        ),
                        bgcolor="#121212",
                        border_radius=8,
                    )
                )
            status_text.value = "Выберите трек для воспроизведения"
        except Exception as ex:
            status_text.value = f"Ошибка поиска: {ex}"
        page.update()

    def play_track(url, title):
        status_text.value = f"⏳ Загрузка потока: {title}"
        page.update()
        threading.Thread(
            target=stream_audio, args=(url, title), daemon=True
        ).start()

    def stream_audio(url, title):
        nonlocal is_playing
        # Предпочитаем m4a для лучшей совместимости с мобильным плеером Android
        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio",
            "quiet": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                stream_url = info["url"]

            audio_player.src = stream_url
            audio_player.autoplay = True
            audio_player.update()

            is_playing = True
            play_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED
            status_text.value = f"🎵 {title}"
        except Exception as ex:
            status_text.value = f"Ошибка воспроизведения: {ex}"
        page.update()

    def toggle_play(e):
        nonlocal is_playing
        if is_playing:
            audio_player.pause()
            play_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED
            is_playing = False
        else:
            audio_player.resume()
            play_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED
            is_playing = True
        page.update()

    play_btn = ft.IconButton(
        icon=ft.Icons.PLAY_CIRCLE_FILLED,
        icon_size=42,
        icon_color="#ff0000",
        on_click=toggle_play,
    )

    # Верхняя панель поиска
    search_bar = ft.Row(
        [
            search_input,
            ft.IconButton(
                icon=ft.Icons.SEARCH,
                icon_color="white",
                bgcolor="#ff0000",
                on_click=search_music,
            ),
        ]
    )

    # Нижняя панель плеера
    player_bar = ft.Container(
        content=ft.Row(
            [ft.Container(content=status_text, expand=True), play_btn],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        bgcolor="#181818",
        padding=ft.padding.symmetric(horizontal=15, vertical=8),
        border_radius=12,
    )

    page.add(search_bar, ft.Divider(color="transparent", height=5), results_list, player_bar)


ft.app(target=main)
