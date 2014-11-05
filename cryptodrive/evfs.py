#!/usr/bin/env python

import os
import errno
from collections import defaultdict
import tempfile
import shutil

from fuse import FUSE, FuseOSError, Operations

from util import encrypt, decrypt

#set for debug/dev
KEY = 'AWaRttWO1t-YDQldf7ebZQkhy3AVy-xvME1WMVEb54E='


class EVFS(Operations):
    def __init__(self, root):
        tmp_dir = os.path.join(tempfile.gettempdir(), 'cryptobox')

        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.mkdir(tmp_dir)

        self.root = root
        self.dirty = defaultdict(bool)
        self.opens = defaultdict(int)

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def _tmp_full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        tmp = tempfile.gettempdir()
        path = os.path.join(tmp, 'cryptobox', partial)
        return path

    #Filesystem operations
    ##########################################################################

    def access(self, path, mode):
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in
                    ('st_atime', 'st_ctime', 'st_gid', 'st_mode',
                     'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in
                    ('f_bavail', 'f_bfree', 'f_blocks', 'f_bsize', 'f_favail',
                     'f_ffree', 'f_files', 'f_flag', 'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, target, name):
        return os.symlink(self._full_path(target), self._full_path(name))

    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    #File operations
    ##########################################################################

    def open(self, path, flags):
        print "OPEN", path, flags
        self.opens[path] += 1

        full_path = self._full_path(path)
        tmp_path = self._tmp_full_path(path)

        with open(full_path, 'rb') as f:
            raw = f.read()

        if len(raw) > 0:
            dirs = os.path.dirname(tmp_path)
            if not os.path.exists(dirs):
                os.makedirs(dirs)
            with open(tmp_path, 'wb') as f:
                f.write(decrypt(KEY, raw))

        return os.open(tmp_path, flags)

    def create(self, path, mode, fi=None):
        print "CREATE", path, mode
        #create both /tmp/path and /root/path
        full_path = self._full_path(path)
        tmp_path = self._tmp_full_path(path)
        os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)
        dirs = os.path.dirname(tmp_path)
        if not os.path.exists(dirs):
            os.makedirs(dirs)
        return os.open(tmp_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        print "READ", path, length, offset, fh
        #read from /tmp/path
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        print "WRITE", path, len(buf), offset, fh
        #write to /tmp/path
        self.dirty[path] = True
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        print "TRUNCATE", path, length, fh
        tmp_path = self._tmp_full_path(path)
        with open(tmp_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        print "FLUSH", path, fh
        return os.fsync(fh)

    def fsync(self, path, fdatasync, fh):
        print "FSYNC", path, fdatasync, fh
        return self.flush(path, fh)

    def release(self, path, fh):
        print "RELEASE", path, fh
        self.opens[path] -= 1

        # encrypt and write if dirty
        if self.dirty[path]:
            print "TRYING TO WRITE"
            #copy enc(/tmp/path file) to /root/path
            with open(self._tmp_full_path(path), 'rb') as f:
                data = f.read()
            with open(self._full_path(path), 'wb') as f:
                f.write(encrypt(KEY, data))
            self.dirty[path] = False

        self.cleanup()
        return os.close(fh)

    def cleanup(self):
        print "RUNNING GARBAGE COLLECTION"
        print self.opens

        #TODO: make this threaded
        for _file in self.opens.keys():
            if self.opens[_file] <= 0:
                os.unlink(self._tmp_full_path(_file))
                del self.opens[_file]

            # Remove the file from dirty list
            if _file in self.dirty:
                del self.dirty[_file]


def main(mountpoint, root):
    FUSE(EVFS(root), mountpoint, foreground=True)


if __name__ == '__main__':
    main('mnt', 'root')