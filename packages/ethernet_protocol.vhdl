-- ///////////////Documentation////////////////////
-- Package for custom ethernet protocol. The protocol
-- should contain transactions of handshaking, data
-- transfer, acknowledgement, retransmision, etc.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

package ethernet_protocol is
    type ether_byte is array(7 downto 0) of std_logic;
    type ether_word is array(natural range <>) of ether_byte;
    
    constant ETHER_PREAMBLE         :   ether_word(0 to 6) := (others => x"55"); -- Preamble
    constant ETHER_SFD              :   ether_word(0 to 0) := (0 => x"D5"); -- Start of frame delimiter
    constant ETHER_BROADCAST_MAC    :   ether_word(0 to 5) := (others => x"FF"); -- Broadcast MAC address
    constant ETHER_FPGA_MAC         :   ether_word(0 to 5) := (0 => x"02", 1 => x"00", 2 => x"46", 3 => x"50", 4 => x"47", 5 => x"41"); -- FPGA MAC address, literally "FPGA"
    constant ETHER_ETHERTYPE_1      :   ether_word(0 to 1) := (0 => x"88", 1 => x"B5"); -- Local experimental ethernet type 1, used for general purpose
    constant ETHER_ETHERTYPE_2      :   ether_word(0 to 1) := (0 => x"88", 1 => x"B6"); -- Local experimental ethernet type 2, used for large data transmission
    constant ETHER_CRC32            :   ether_word(0 to 3) := (0 => x"04", 1 => x"C1", 2 => x"1D", 3 => x"B7"); -- CRC32 polynomial
    -- This protocol is dedicated for large data transmission from FPGA to PC.
    -- General transmissions and data transfer employ different protocols.
    -- Protocol x"88B5" is used for handshakes, start/end of session, etc.
    -- The data segment of each packet is 46 bytes long, where the first byte
    -- indicates the type of transaction, the second byte indicates the action
    -- of the transaction, and the following 44 bytes are reserved for data.
    -- A session begins with a handshake transaction, where the FPGA queries
    -- the MAC address of an available PC, which runs a custom python script
    -- to handle the protocol.
    ------------------ Handshake Query Packet ------------------
    -- /----------------\/----------\/---------\/-----------\/----------\/------\/---------\/----\
    -- | PREAMBLE + SFD | BROADCAST | FPGA_MAC | ETHERTYPE1 | HANDSHAKE | QUERY | reserved | FCS |
    -- \----------------/\----------/\---------/\-----------/\----------/\------/\---------/\----/
    --         8              6          6           2            1         1        44       4    bytes
    constant ETHER_HANDSHAKE_TRANSACTION    :   ether_word(0 to 0) := (0 => x"01"); -- Handshake transaction
    constant ETHER_HANDSHAKE_ACTION_QUERY   :   ether_word(0 to 0) := (0 => x"01"); -- Query MAC address
    -- After receiving the handshake packet, the PC immediately replies
    -- with an acknowledgement packet, which contains the MAC address of
    -- the PC in the header.
    -- Nothing will be sent if the packet did not pass the CRC check.
    ------------------ Handshake ACK Packet ------------------
    -- /----------------\/---------\/-------\/-----------\/----------\/----\/---------\/----\
    -- | PREAMBLE + SFD | FPGA_MAC | PC_MAC | ETHERTYPE1 | HANDSHAKE | ACK | reserved | FCS |
    -- \----------------/\---------/\-------/\-----------/\----------/\----/\---------/\----/
    --         8             6         6          2            1        1       44       4    bytes
    constant ETHER_HANDSHAKE_ACTION_ACK : ether_word(0 to 0) := (0 => x"02"); -- Acknowledge MAC address
    -- If no response is received, or the packet is invalid, the FPGA
    -- repeats the query for a given number of times.
    constant ETHER_HANDSHAKE_TIMEOUT : integer := 100; -- Timeout in ms
    constant ETHER_HANDSHAKE_RETRY_LIMIT : integer := 3; -- Retry limit
    -- After the handshake succeeds, the FPGA sends a session start query
    -- packet to the PC, which contains the total number of data frames.
    ------------------ Session Start Query Packet ------------------
    -- /----------------\/-------\/---------\/-----------\/--------------\/------\/-------\/---------\/----\
    -- | PREAMBLE + SFD | PC_MAC | FPGA_MAC | ETHERTYPE1 | SESSION START | QUERY | frames | reserved | FCS |
    -- \----------------/\-------/\---------/\-----------/\--------------/\------/\-------/\---------/\----/
    --         8             6         6          2              1           1        4        40       4    bytes
    constant ETHER_SESSION_START_TRANSACTION : ether_word(0 to 0) := (0 => x"02"); -- Session start transaction
    constant ETHER_SESSION_START_ACTION_QUERY : ether_word(0 to 0) := (0 => x"01"); -- Query session start
    -- The PC replies with a session start acknowledge packet, which indicates
    -- the session is ready to begin.
    -- Nothing will be sent if the packet did not pass the CRC check.
    ------------------ Session Start ACK Packet ------------------
    -- /----------------\/---------\/-------\/-----------\/--------------\/----\/---------\/----\
    -- | PREAMBLE + SFD | FPGA_MAC | PC_MAC | ETHERTYPE1 | SESSION START | ACK | reserved | FCS |
    -- \----------------/\---------/\-------/\-----------/\--------------/\----/\---------/\----/
    --         8             6         6          2              1          1       44       4    bytes
    constant ETHER_SESSION_START_ACTION_ACK : ether_word(0 to 0) := (0 => x"02"); -- Acknowledge session start
    -- If no response is received, or the packet is invalid, the FPGA
    -- immediately terminates the transmission and returns a failure
    -- through the UART interface.
    constant ETHER_SESSION_START_TIMEOUT : integer := 100; -- Timeout in ms
    -- Data transmission is carried out on ether type x"88B6".
    -- The data segment of each data frame should be exactly
    -- 1500 bytes long except for the last frame, where the
    -- first four bytes indicate the frame number, and the
    -- following two bytes indicate the length of the data
    -- segment(including the header).
    ------------------ Data Frame Packet ------------------
    -- /----------------\/-------\/---------\/-----------\/-------------\/------------\/-----\/----\
    -- | PREAMBLE + SFD | PC_MAC | FPGA_MAC | ETHERTYPE2 | frame number | data length | data | FCS |
    -- \----------------/\-------/\---------/\-----------/\-------------/\------------/\-----/\----/
    --         8             6         6          2             4              2       1~1494   4    bytes
    -- After each data frame is sent, the FPGA waits for an
    -- acknowledgement packet from the PC, which contains the
    -- correct frame number.
    -- If the packet did not pass the CRC check, the PC sends
    -- an error packet, which contains the correct frame number.
    ------------------ Data Frame ACK Packet ------------------
    -- /----------------\/---------\/-------\/-----------\/-----------\/----\/---------\/----\
    -- | PREAMBLE + SFD | FPGA_MAC | PC_MAC | ETHERTYPE1 | DATA FRAME | ACK | reserved | FCS |
    -- \----------------/\---------/\-------/\-----------/\-----------/\----/\---------/\----/
    --         8             6         6          2            1         1       44       4    bytes
    -- The frame number should follow the action byte.
    constant ETHER_DATA_FRAME_TRANSACTION : ether_word(0 to 0) := (0 => x"03"); -- Data frame transaction
    constant ETHER_DATA_FRAME_ACTION_ACK : ether_word(0 to 0) := (0 => x"02"); -- Acknowledge data frame
    constant ETHER_DATA_FRAME_ACTION_ERR : ether_word(0 to 0) := (0 => x"03"); -- Error data frame
    -- If no response is received, or the packet is invalid, the FPGA
    -- immediately terminates the transmission and returns a failure
    -- through the UART interface.
    constant ETHER_DATA_FRAME_TIMEOUT : integer := 100; -- Timeout in ms
    -- Otherwise, if the PC requires a retransmission, the FPGA retries
    -- the data frame until the PC acknowledges with the correct frame
    -- number.
    -- The total number of retries in a whole session should be limited
    -- to a certain number. Otherwise, the FPGA terminates the transmission
    -- and returns a failure through the UART interface.
    -- The FPGA should maintain a memory buffer for recent bytes in the transmission stream.
    constant ETHER_DATA_FRAME_RETRY_LIMIT : integer := 1; -- Retry limit
    -- After the last data frame is sent, the FPGA sends a session end
    -- query packet to the PC.
    ------------------ Session End Query Packet ------------------
    -- /----------------\/-------\/---------\/-----------\/------------\/------\/---------\/----\
    -- | PREAMBLE + SFD | PC_MAC | FPGA_MAC | ETHERTYPE1 | SESSION END | QUERY | reserved | FCS |
    -- \----------------/\-------/\---------/\-----------/\------------/\------/\---------/\----/
    --         8             6         6          2             1          1        44       4    bytes
    constant ETHER_SESSION_END_TRANSACTION : ether_word(0 to 0) := (0 => x"04"); -- Session end transaction
    constant ETHER_SESSION_END_ACTION_QUERY : ether_word(0 to 0) := (0 => x"01"); -- Query session end
    -- The PC replies with a session end acknowledge packet, which indicates
    -- the formal end of the session. 
    -- Nothing will be sent if the packet did not pass the CRC check.
    ------------------ Session End ACK Packet ------------------
    -- /----------------\/---------\/-------\/-----------\/------------\/----\/---------\/----\
    -- | PREAMBLE + SFD | FPGA_MAC | PC_MAC | ETHERTYPE1 | SESSION END | ACK | reserved | FCS |
    -- \----------------/\---------/\-------/\-----------/\------------/\----/\---------/\----/
    --         8             6         6          2             1         1       44       4    bytes
    constant ETHER_SESSION_END_ACTION_ACK : ether_word(0 to 0) := (0 => x"02"); -- Acknowledge session end
    -- After this packet is received, the FPGA should send a message
    -- through the UART interface to inform that the transmission
    -- has just ended.
    -- If no response is received, or the packet is invalid, the FPGA
    -- immediately terminates the transmission and returns a failure
    -- through the UART interface, even if the last data frame was
    -- successfully sent.

    -- Following are constants defined for the implementation of the ethernet interface instead of the protocol.
    constant ETHER_STATUS_IDLE : std_logic_vector(3 downto 0) := x"0";
    constant ETHER_STATUS_INITIALIZING : std_logic_vector(3 downto 0) := x"1";
    constant ETHER_STATUS_TRANSMITTING : std_logic_vector(3 downto 0) := x"2";
    constant ETHER_STATUS_LISTENING : std_logic_vector(3 downto 0) := x"3";
    constant ETHER_STATUS_RECEIVING : std_logic_vector(3 downto 0) := x"4";
    constant ETHER_STATUS_ERROR : std_logic_vector(3 downto 0) := x"5";
    constant ETHER_STATUS_TIMEOUT : std_logic_vector(3 downto 0) := x"6";
    constant ETHER_STATUS_SUCCESS : std_logic_vector(3 downto 0) := x"7";    
end package ethernet_protocol;