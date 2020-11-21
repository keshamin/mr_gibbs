import enum


class TorrentStatus(enum.Enum):
    STOPPED = 0
    CHECK_PENDING = 1
    CHECKING = 2
    DOWNLOAD_PENDING = 3
    DOWNLOADING = 4
    SEED_PENDING = 5
    SEEDING = 6


status_to_emoji = {
    TorrentStatus.STOPPED: '⛔️',
    TorrentStatus.CHECK_PENDING: '💬',
    TorrentStatus.CHECKING: '💬',
    TorrentStatus.DOWNLOAD_PENDING: '💬',
    TorrentStatus.DOWNLOADING: '⏬',
    TorrentStatus.SEED_PENDING: '💬',
    TorrentStatus.SEEDING: '✅',
}
