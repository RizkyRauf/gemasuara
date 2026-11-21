import argparse
import logging
import sys
from pathlib import Path

from auth import exchange_code, get_auth_url, list_accounts
from content import (
    MAX_CAPTION_LENGTH,
    create_content,
    delete_content,
    get_alias,
    list_aliases,
    load_all_content,
    load_content,
    mark_failed,
    mark_posted,
    remove_alias,
    set_alias,
    summary,
    update_content,
)
from upload import direct_post_video, upload_draft_video

LOGS_DIR = Path(__file__).parent / "logs"


def _setup_logging():
    LOGS_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR / "tiktok_uploader.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def cmd_auth(args):
    """Generate URL OAuth dan tukar authorization code jadi token."""
    url, state = get_auth_url()

    print("Buka URL berikut di browser, lalu login ke akun TikTok kamu:")
    print(url)
    print()
    print("Setelah di-redirect, copy nilai 'code' dari URL callback dan paste di bawah.")

    code = input("Authorization code: ").strip()
    if not code:
        print("Code tidak boleh kosong.")
        sys.exit(1)

    token = exchange_code(code)
    print()
    print("Login berhasil!")
    print(f"Open ID : {token.get('open_id')}")
    print(f"Scope   : {token.get('scope')}")
    print("Token sudah disimpan di tokens.json")


def cmd_accounts(args):
    """Tampilkan daftar akun yang sudah login dan alias yang tersimpan."""
    accounts = list_accounts()
    aliases = list_aliases()

    if not accounts:
        print("Belum ada akun yang login. Jalankan: python main.py auth")
    else:
        print("Akun yang sudah login:")
        for acc in accounts:
            open_id = acc["open_id"]
            alias = get_alias(open_id)
            alias_display = f" (alias: {alias})" if alias else ""
            print(f"- {open_id}{alias_display} | scope: {acc['scope']}")

    if aliases:
        print()
        print("Alias yang tersimpan:")
        for alias, open_id in sorted(aliases.items()):
            print(f"- {alias} -> {open_id}")


def cmd_accounts_alias(args):
    """Set alias untuk akun."""
    set_alias(args.open_id, args.alias)
    print(f"Alias '{args.alias}' -> '{args.open_id}' disimpan.")


def cmd_accounts_unalias(args):
    """Hapus alias akun."""
    remove_alias(args.alias)
    print(f"Alias '{args.alias}' dihapus.")


def cmd_content_add(args):
    """Buat konten baru untuk akun tertentu."""
    content = create_content(
        account=args.account,
        video_path=args.video,
        title=args.title,
        caption=args.caption,
        post_mode=args.mode,
        planned_at=args.planned_at,
        notes=args.notes or "",
    )
    print(f"Konten dibuat: {content.id}")
    print(f"  Akun     : {content.account_id}")
    print(f"  Folder   : {content.dir}")
    print(f"  Status   : {content.status}")
    print(f"  Post mode: {content.post_mode}")


def cmd_content_list(args):
    """Tampilkan daftar konten."""
    account = args.account
    status = args.status
    items = load_all_content(account=account, status=status)

    if not items:
        print("Tidak ada konten yang cocok.")
        return

    print(f"{'ID':<10} | {'Account':<15} | {'Status':<7} | {'Title':<30} | {'Created'}")
    print("-" * 85)
    for item in items:
        display_account = get_alias(item.account_id) or item.account_id[:14]
        print(f"{item.id:<10} | {display_account:<15} | {item.status:<7} | "
              f"{item.title[:30]:<30} | {item.created_at[:10]}")


def cmd_content_show(args):
    """Tampilkan detail satu konten."""
    content = load_content(args.content_id)
    print(f"ID         : {content.id}")
    print(f"Account    : {content.account_id}")
    print(f"Alias      : {get_alias(content.account_id) or '-'}")
    print(f"Title      : {content.title}")
    print(f"Caption    : {content.caption}")
    print(f"Status     : {content.status}")
    print(f"Post mode  : {content.post_mode}")
    print(f"Planned at : {content.planned_at or '-'}")
    print(f"Notes      : {content.notes or '-'}")
    print(f"Created    : {content.created_at}")
    print(f"Updated    : {content.updated_at}")
    print(f"Posted at  : {content.posted_at or '-'}")
    print(f"Publish ID : {content.publish_id or '-'}")
    print(f"Failed at  : {content.failed_at or '-'}")
    if content.last_error:
        print(f"Last error : {content.last_error}")
    print(f"Video path : {content.video_path}")


def cmd_content_edit(args):
    """Edit metadata konten."""
    content = update_content(
        content_id=args.content_id,
        title=args.title,
        caption=args.caption,
        status=args.status,
        post_mode=args.mode,
        planned_at=args.planned_at,
        notes=args.notes,
    )
    print(f"Konten '{content.id}' diperbarui.")


def cmd_content_ready(args):
    """Pindahkan konten dari draft ke ready dengan validasi."""
    content = load_content(args.content_id)
    if not content.video_path.exists():
        print("Error: File video tidak ditemukan.")
        sys.exit(1)
    if not content.caption or not content.caption.strip():
        print("Error: Caption tidak boleh kosong.")
        sys.exit(1)
    if len(content.caption) > MAX_CAPTION_LENGTH:
        print(f"Error: Caption melebihi {MAX_CAPTION_LENGTH} karakter.")
        sys.exit(1)

    content = update_content(args.content_id, status="ready")
    print(f"Konten '{content.id}' sekarang status: ready")


def cmd_content_post(args):
    """Posting konten ke TikTok."""
    content = load_content(args.content_id)

    if content.status not in {"ready", "failed"}:
        print(f"Error: Konten harus status 'ready' atau 'failed', saat ini '{content.status}'.")
        print("Jalankan: python main.py content ready <content_id>")
        sys.exit(1)

    post_mode = args.mode or content.post_mode
    account_display = get_alias(content.account_id) or content.account_id

    try:
        if post_mode == "direct":
            publish_id, _ = direct_post_video(
                content.account_id,
                content.video_path,
                content.caption,
            )
        else:
            publish_id, _ = upload_draft_video(
                content.account_id,
                content.video_path,
            )
        mark_posted(content.id, publish_id)
        print(f"Posting berhasil! Publish ID: {publish_id}")
        print(f"Akun: {account_display} | Mode: {post_mode}")
    except Exception as exc:
        mark_failed(content.id, str(exc))
        print(f"Posting gagal: {exc}")
        sys.exit(1)


def cmd_content_delete(args):
    """Hapus konten secara permanen."""
    content = load_content(args.content_id)
    if not args.yes:
        confirm = input(f"Yakin hapus konten '{content.title}' ({content.id})? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Dibatalkan.")
            return
    delete_content(args.content_id)
    print(f"Konten '{args.content_id}' dihapus.")


def cmd_content_summary(args):
    """Tampilkan ringkasan konten per akun."""
    data = summary()
    if not data:
        print("Belum ada konten.")
        return

    print(f"{'Account':<15} | {'draft':>5} | {'ready':>5} | {'posted':>6} | {'failed':>6} | {'total':>5}")
    print("-" * 65)
    totals = {"draft": 0, "ready": 0, "posted": 0, "failed": 0, "total": 0}
    for account, counts in sorted(data.items()):
        print(f"{account:<15} | {counts['draft']:>5} | {counts['ready']:>5} | "
              f"{counts['posted']:>6} | {counts['failed']:>6} | {counts['total']:>5}")
        for key in totals:
            totals[key] += counts[key]
    print("-" * 65)
    print(f"{'TOTAL':<15} | {totals['draft']:>5} | {totals['ready']:>5} | "
          f"{totals['posted']:>6} | {totals['failed']:>6} | {totals['total']:>5}")


def main():
    _setup_logging()

    parser = argparse.ArgumentParser(description="TikTok Content Uploader (official API)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # auth
    auth_parser = subparsers.add_parser("auth", help="Login akun TikTok dan simpan token")
    auth_parser.set_defaults(func=cmd_auth)

    # accounts
    accounts_parser = subparsers.add_parser("accounts", help="Lihat akun yang sudah login")
    accounts_parser.set_defaults(func=cmd_accounts)

    accounts_sub = accounts_parser.add_subparsers(dest="accounts_command")
    alias_parser = accounts_sub.add_parser("alias", help="Set alias untuk open_id")
    alias_parser.add_argument("open_id", help="Open ID akun")
    alias_parser.add_argument("alias", help="Alias yang diinginkan")
    alias_parser.set_defaults(func=cmd_accounts_alias)

    unalias_parser = accounts_sub.add_parser("unalias", help="Hapus alias")
    unalias_parser.add_argument("alias", help="Alias yang akan dihapus")
    unalias_parser.set_defaults(func=cmd_accounts_unalias)

    # content
    content_parser = subparsers.add_parser("content", help="Kelola konten")
    content_sub = content_parser.add_subparsers(dest="content_command", required=True)

    add_parser = content_sub.add_parser("add", help="Buat konten baru")
    add_parser.add_argument("--account", required=True, help="Alias atau open_id akun")
    add_parser.add_argument("--video", required=True, help="Path file video")
    add_parser.add_argument("--title", required=True, help="Judul internal konten")
    add_parser.add_argument("--caption", required=True, help="Caption untuk posting")
    add_parser.add_argument("--mode", choices=["direct", "draft"], default="draft",
                            help="Mode posting default untuk konten ini")
    add_parser.add_argument("--planned-at", default=None, help="Rencana tanggal posting (ISO 8601)")
    add_parser.add_argument("--notes", default=None, help="Catatan internal")
    add_parser.set_defaults(func=cmd_content_add)

    list_parser = content_sub.add_parser("list", help="Daftar konten")
    list_parser.add_argument("--account", default=None, help="Filter per akun")
    list_parser.add_argument("--status", default=None, choices=["draft", "ready", "posted", "failed"],
                             help="Filter per status")
    list_parser.set_defaults(func=cmd_content_list)

    show_parser = content_sub.add_parser("show", help="Detail konten")
    show_parser.add_argument("content_id", help="ID konten")
    show_parser.set_defaults(func=cmd_content_show)

    edit_parser = content_sub.add_parser("edit", help="Edit metadata konten")
    edit_parser.add_argument("content_id", help="ID konten")
    edit_parser.add_argument("--title", default=None, help="Judul baru")
    edit_parser.add_argument("--caption", default=None, help="Caption baru")
    edit_parser.add_argument("--status", default=None, choices=["draft", "ready", "posted", "failed"],
                             help="Status baru")
    edit_parser.add_argument("--mode", default=None, choices=["direct", "draft"],
                             help="Mode posting baru")
    edit_parser.add_argument("--planned-at", default=None, help="Rencana tanggal posting baru")
    edit_parser.add_argument("--notes", default=None, help="Catatan baru")
    edit_parser.set_defaults(func=cmd_content_edit)

    ready_parser = content_sub.add_parser("ready", help="Validasi dan ubah status jadi ready")
    ready_parser.add_argument("content_id", help="ID konten")
    ready_parser.set_defaults(func=cmd_content_ready)

    post_parser = content_sub.add_parser("post", help="Posting konten ke TikTok")
    post_parser.add_argument("content_id", help="ID konten")
    post_parser.add_argument("--mode", default=None, choices=["direct", "draft"],
                             help="Override mode posting")
    post_parser.set_defaults(func=cmd_content_post)

    delete_parser = content_sub.add_parser("delete", help="Hapus konten")
    delete_parser.add_argument("content_id", help="ID konten")
    delete_parser.add_argument("--yes", action="store_true", help="Langsung hapus tanpa konfirmasi")
    delete_parser.set_defaults(func=cmd_content_delete)

    summary_parser = content_sub.add_parser("summary", help="Ringkasan konten per akun")
    summary_parser.set_defaults(func=cmd_content_summary)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
