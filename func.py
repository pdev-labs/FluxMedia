def run_ydl_download(ydl_opts: Dict[str, Any], urls: List[str], downloaded_files: Optional[List[str]]=None) -> bool:
    """Runs a yt-dlp session inside a Rich Progress context manager."""
    with Progress(TextColumn('[bold blue]{task.description}'), BarColumn(bar_width=40), DownloadColumn(), TransferSpeedColumn(), TimeRemainingColumn(), console=console) as progress:
        hook = RichProgressHook(progress, downloaded_files)
        ydl_opts['progress_hooks'] = [hook]

        def pp_hook(d):
            if d.get('status') == 'finished' and downloaded_files is not None:
                filepath = d.get('filepath')
                if filepath and filepath not in downloaded_files:
                    downloaded_files.append(filepath)
        ydl_opts['postprocessor_hooks'] = [pp_hook]
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return_code = ydl.download(urls)
            return return_code == 0
        except KeyboardInterrupt:
            logger.warning('Download interrupted by user (KeyboardInterrupt).')
            console.print('\n[bold yellow]Download cancelled by user.[/bold yellow]')
            raise KeyboardInterrupt
        except Exception as e:
            logger.error(f'yt-dlp download execution encountered an error: {e}', exc_info=True)
            console.print(f'\n[bold red]Download Error: {e}[/bold red]')
            if ydl_opts.get('cookiesfrombrowser'):
                console.print("[cyan]💡 Tip: If you get browser cookie access errors, try changing 'Cookies Browser' to 'none' in Settings.[/cyan]")
            return False