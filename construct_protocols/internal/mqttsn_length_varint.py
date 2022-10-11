import io
from construct import Construct, Subconstruct, Byte, Int16ub, GreedyBytes, IntegerError, singleton, stream_read, stream_write, stream_tell


@singleton
class MQTTSNLengthVarInt(Construct):

    def _parse(self, stream, context, path):
        first_byte = stream_read(stream, 1, path)
        if first_byte != b"\x01":
            return Byte.parse(first_byte)
        else:
            rest = stream_read(stream, 2, path)
            return Int16ub.parse(rest)

    def _build(self, obj, stream, context, path):
        if not isinstance(obj, int):
            raise IntegerError(f"value {obj} is not an integer", path=path)
        if not 2 <= obj <= 65535:
            raise IntegerError(f"Length must be between 2 and 65535, is {obj}",
                               path=path)

        if obj > 255:
            stream_write(stream, b"\x01" + Int16ub.build(obj), 3, path)
        else:
            stream_write(stream, Byte.build(obj), 1, path)


class MQTTSNLengthPrefixed(Subconstruct):
    subcon: Construct

    def __init__(self, subcon: Construct):
        super().__init__(subcon)
        self.subcon = subcon

    def _parse(self, stream, context, path):
        start_tell = stream_tell(stream, path)
        length = MQTTSNLengthVarInt._parsereport(stream, context, path)
        lengthfield_length = stream_tell(stream, path) - start_tell
        subcons_length = length - lengthfield_length

        data = stream_read(stream, subcons_length, path)
        if self.subcon is GreedyBytes:
            return data
        else:
            return self.subcon._parsereport(io.BytesIO(data), context, path)

    def _build(self, obj, stream, context, path):
        stream2 = io.BytesIO()
        buildret = self.subcon._build(obj, stream2, context, path)
        data = stream2.getvalue()
        length = len(data)

        if length > 254:
            length += 3
        else:
            length += 1

        MQTTSNLengthVarInt._build(length, stream, context, path)
        stream_write(stream, data, len(data), path)
        return buildret

    def _sizeof(self, context, path):
        return super()._sizeof(context, path)
