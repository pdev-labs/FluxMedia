def main():
    """Primary routing flow block."""
    import argparse
    parser = argparse.ArgumentParser(description='FluxMedia CLI - Command-Line Media Downloader')
    parser.add_argument('urls', nargs='*', help='URLs to download')
    parser.add_argument('-a', '--audio', action='store_true', help='Download audio only')
    parser.add_argument('-o', '--output', type=str, help='Destination directory')
    args, unknown = parser.parse_known_args()
    if args.urls:
        verify_and_install_requirements()
        init_dependencies()
        config = load_config()
        global CLEAN_LOGS_ENABLED
        CLEAN_LOGS_ENABLED = config.get('clean_logs_enabled', True)
        dest_dir = args.output if args.output else config.get('download_dir', os.path.join(os.path.expanduser('~'), 'Downloads'))
        os.makedirs(dest_dir, exist_ok=True)
        ffmpeg_available = shutil.which('ffmpeg') is not None
        valid_urls = []
        for u in args.urls:
            n = normalize_and_validate_url(u)
            if n:
                valid_urls.append(n)
        if not valid_urls:
            print('No valid URLs provided.')
            sys.exit(1)
        if args.audio:
            ydl_opts = {'format': 'bestaudio/best', 'outtmpl': os.path.join(dest_dir, config['filename_format']), 'quiet': True, 'no_warnings': True, 'noprogress': True}
            if ffmpeg_available:
                ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': config.get('audio_format', 'mp3'), 'preferredquality': '192'}]
        else:
            format_str = get_format_string('10', ffmpeg_available)
            ydl_opts = {'format': format_str, 'outtmpl': os.path.join(dest_dir, config['filename_format']), 'quiet': True, 'no_warnings': True, 'noprogress': True}
            if ffmpeg_available:
                ydl_opts['merge_output_format'] = config.get('video_format', 'default') if config.get('video_format', 'default') != 'default' else 'mp4'
        ydl_opts = apply_common_ydl_opts(ydl_opts, config)
        print(f'Downloading {len(valid_urls)} item(s) to {dest_dir}...')
        run_ydl_download(ydl_opts, valid_urls)
        sys.exit(0)
    verify_and_install_requirements()
    init_dependencies()
    check_fluxmedia_update_sync()
    start_version_check()
    config = load_config()
    CLEAN_LOGS_ENABLED = config.get('clean_logs_enabled', True)
    apply_theme_colors(config.get('theme', 'dark'))
    if config.get('show_educational_notice', True):
        print_header()
        notice_text = Text()
        notice_text.append('\n⚠️  IMPORTANT DISCLAIMER & NOTICE ⚠️\n\n', style='bold yellow')
        notice_text.append('This python program is just for educational purposes.\n', style='bold white')
        notice_text.append('You should take permission from the original video creator to download this video.\n\n', style='bold white')
        notice_text.append('By continuing, you agree that you will use this tool responsibly and legally.\n', style='italic gray')
        notice_text.append('(You can disable this notice in Settings)\n', style='dim cyan')
        console.print(Panel(Align.center(notice_text), title='[bold red]Disclaimer Notice[/bold red]', border_style='red', padding=(1, 2)))
        choice = Prompt.ask('Choose an action', choices=['Understood', 'Exit'], default='Exit')
        if choice == 'Exit':
            console.print('\n[bold red]Exiting...[/bold red]')
            sys.exit(0)
        console.print('[green]Thank you! Loading FluxMedia...[/green]')
        import time
        time.sleep(1.0)
    while True:
        try:
            print_header()
            dl_table = Table(show_header=False, box=None, padding=(0, 1))
            dl_table.add_row('[bold yellow]0.[/bold yellow] Launch Advanced TUI Mode [dim](New)[/dim]')
            dl_table.add_row('[bold cyan]1.[/bold cyan] Download Video [dim](URL)[/dim]')
            dl_table.add_row('[bold cyan]2.[/bold cyan] Search & Download [dim](YT)[/dim]')
            dl_table.add_row('[bold cyan]3.[/bold cyan] Download Audio [dim](MP3)[/dim]')
            dl_table.add_row('[bold cyan]4.[/bold cyan] Download Playlist [dim](Batch)[/dim]')
            dl_table.add_row('[bold cyan]5.[/bold cyan] Download Channel [dim](Batch)[/dim]')
            dl_table.add_row('[bold cyan]6.[/bold cyan] Download Subtitles [dim](Subs)[/dim]')
            dl_table.add_row('[bold cyan]7.[/bold cyan] Trim & Download [dim](Trimmer)[/dim]')
            mgmt_table = Table(show_header=False, box=None, padding=(0, 1))
            mgmt_table.add_row('[bold green]8.[/bold green] View History Logs')
            mgmt_table.add_row('[bold green]9.[/bold green] Download Queue [dim](Batch)[/dim]')
            mgmt_table.add_row('[bold green]10.[/bold green] Configuration [dim](Settings)[/dim]')
            mgmt_table.add_row('[bold green]11.[/bold green] Updates Manager')
            mgmt_table.add_row('[bold green]12.[/bold green] Open Save Folder')
            mgmt_table.add_row('[bold green]13.[/bold green] Transcode Media [dim](Converter)[/dim]')
            mgmt_table.add_row('[bold green]14.[/bold green] Share via QR-Code [dim](LAN)[/dim]')
            info_table = Table(show_header=False, box=None, padding=(0, 1))
            info_table.add_row('[bold magenta]15.[/bold magenta] Troubleshooting [dim](FAQ)[/dim]')
            info_table.add_row('[bold magenta]16.[/bold magenta] About Creator [dim](Credit)[/dim]')
            info_table.add_row('[bold magenta]17.[/bold magenta] Send Feedback [dim](Bugs)[/dim]')
            info_table.add_row('[bold red]18.[/bold red] Exit Application [dim](Quit)[/dim]')
            menu_grid = Table.grid(expand=True)
            if console.width >= 100:
                menu_grid.add_column(ratio=1)
                menu_grid.add_column(ratio=1)
                menu_grid.add_column(ratio=1)
                menu_grid.add_row(Panel(dl_table, title='[bold cyan]📥 Downloader Engine[/bold cyan]', border_style='cyan', padding=(1, 2)), Panel(mgmt_table, title='[bold green]⚙️ Workspace & Settings[/bold green]', border_style='green', padding=(1, 2)), Panel(info_table, title='[bold magenta]ℹ️ System Info[/bold magenta]', border_style='magenta', padding=(1, 2)))
            else:
                menu_grid.add_column(ratio=1)
                menu_grid.add_row(Panel(dl_table, title='[bold cyan]📥 Downloader Engine[/bold cyan]', border_style='cyan', padding=(0, 2)))
                menu_grid.add_row(Panel(mgmt_table, title='[bold green]⚙️ Workspace & Settings[/bold green]', border_style='green', padding=(0, 2)))
                menu_grid.add_row(Panel(info_table, title='[bold magenta]ℹ️ System Info[/bold magenta]', border_style='magenta', padding=(0, 2)))
            console.print(Panel(menu_grid, box=box.DOUBLE, title='[bold white] 🌊 FLUXMEDIA MAIN MENU 🌊 [/bold white]', border_style='bold blue', padding=(1, 2)))
            choice = Prompt.ask('Choose an option', choices=[str(i) for i in range(0, 19)], default='18')
            clear_screen()
            if choice == '0':
                try:
                    from fluxmedia.tui import run_tui
                    run_tui()
                except ImportError as e:
                    console.print(f'[bold red]Failed to load TUI. Ensure textual is installed: {e}[/bold red]')
                    Prompt.ask('\nPress Enter to continue...')
            elif choice == '1':
                operation_download_video(config)
            elif choice == '2':
                operation_search_and_download_video(config)
            elif choice == '3':
                operation_download_audio(config)
            elif choice == '4':
                operation_download_playlist(config)
            elif choice == '5':
                operation_download_channel(config)
            elif choice == '6':
                operation_download_subtitles(config)
            elif choice == '7':
                operation_trim_and_download_video(config)
            elif choice == '8':
                operation_view_history()
            elif choice == '9':
                operation_download_queue(config)
            elif choice == '10':
                config = operation_settings(config)
            elif choice == '11':
                operation_updates_manager(config)
            elif choice == '12':
                operation_open_downloads_folder(config)
            elif choice == '13':
                operation_transcode_media(config)
            elif choice == '14':
                operation_share_via_qr(config)
            elif choice == '15':
                operation_troubleshooting_guide()
            elif choice == '16':
                operation_about_creator()
            elif choice == '17':
                operation_report_bug_feedback()
            elif choice == '18':
                console.print('\n[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]')
                break
        except KeyboardInterrupt:
            if register_interrupt():
                console.print('\n[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]')
                sys.exit(0)
            blink_warning()
        except Exception as e:
            logger.critical(f'Unhandled exception in main loop: {e}', exc_info=True)
            console.print(f'\n[bold red]An unexpected error occurred: {e}[/bold red]')
            console.print(f'Please check {LOG_FILE} for full details.')
            Prompt.ask('\nPress Enter to continue...')