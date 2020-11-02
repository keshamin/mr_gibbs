import transmissionrpc


class TorrentStatuses:
    STOPPED = 'stopped'
    CHECK_PENDING = 'check pending'
    CHECKING = 'checking'
    DOWNLOAD_PENDING = 'download pending'
    DOWNLOADING = 'downloading'
    SEED_PENDING = 'seed pending'
    SEEDING = 'seeding'


class Trans(transmissionrpc.Client):
    """This in a minor extension of transmissionrpc.Client
    """

    def get_tids(self):
        """
        :return: list of all torrents' IDs (tid)
        """
        return [t._fields['id'].value for t in self.get_torrents()]
