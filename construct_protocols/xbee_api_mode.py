from construct import Struct, BitStruct, Const, Switch, BitsInteger, Int16ub, Int64ub, Byte, Flag, Enum, GreedyBytes, Default, Padding, RawCopy, Checksum, Prefixed, this


def calc_checksum(data) -> int:
    checksum = 0
    for byte in data.data:
        checksum = (checksum + byte) % 0x100

    return 0xFF - checksum


APIDataModemStatus = Struct("modem_status" / Byte)

APIDataReceivePacket = Struct(
    "source_address" / Int64ub,
    Padding(2),
    "receive_options" / BitStruct(
        "acknowledged" / Flag,
        "broadcast" / Flag,
        Padding(4),
        "digimesh_delivery_method" / Enum(
            BitsInteger(2),
            point_multipoint=1,
            directed_broadcast=2,
            digimesh=3,
        ),
    ),
    "message" / GreedyBytes,
)

APIDataTransmitRequest = Struct(
    "frame_id" / Default(Byte, 0),
    "destination_address" / Int64ub,
    Padding(2),
    "transmit_radius" / Default(Byte, 0),
    "transmit_options" / Default(Byte, 0),
    "message" / GreedyBytes,
)

APIFrame = Struct(
    "start_delimeter" / Const(b'\x7E'),
    "content" / Prefixed(
        Int16ub,
        RawCopy(
            Struct(
                "frame_type" / Byte,
                "frame_data" / RawCopy(
                    Switch(
                        this.frame_type,
                        {
                            0x10: APIDataTransmitRequest,
                            0x8A: APIDataModemStatus,
                            0x90: APIDataReceivePacket,
                        },
                        default=GreedyBytes,
                    )),
            ))),
    "checksum" / Checksum(Byte, calc_checksum, this.content),
)

if __name__ == "__main__":
    print(APIFrame.parse(bytes.fromhex("7e00022311cb")))
    print(APIFrame.parse(bytes.fromhex("7e00028a0075")))

    # Checksum example from the docs
    assert APIFrame.build({"content": {
        "data": b"\x23\x11"
    }}) == bytes.fromhex("7e00022311cb")
