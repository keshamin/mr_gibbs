from transmission_rpc import Status


status_to_emoji = {
    Status.STOPPED: '⛔️',
    Status.CHECK_PENDING: '💬',
    Status.CHECKING: '💬',
    Status.DOWNLOAD_PENDING: '💬',
    Status.DOWNLOADING: '⏬',
    Status.SEED_PENDING: '💬',
    Status.SEEDING: '✅',
}
