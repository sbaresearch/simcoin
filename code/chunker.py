import os


# http://www.blopig.com/blog/2016/08/processing-large-files-using-python-part-duex/
class Chunker(object):

    # Iterator that yields start and end locations of a file chunk of default size 1MB.
    @classmethod
    def chunkify(cls, file_name, size=1024*1024):
        file_end = os.path.getsize(file_name)
        with open(file_name, 'rb') as file:
            chunk_end = file.tell()
            while True:
                chunk_start = chunk_end
                file.seek(size, 1)
                cls._EOC(file)
                chunk_end = file.tell()
                yield chunk_start, chunk_end - chunk_start
                if chunk_end >= file_end:
                    break

    # Move file pointer to end of chunk
    @staticmethod
    def _EOC(file):
        file.readline()

    # read chunk
    @staticmethod
    def read(file_name, chunk):
        with open(file_name, 'r') as file:
            file.seek(chunk[0])
            return file.read(chunk[1])

    # iterator that splits a chunk into units
    @staticmethod
    def parse(chunk):
        for line in chunk.splitlines():
            yield line
