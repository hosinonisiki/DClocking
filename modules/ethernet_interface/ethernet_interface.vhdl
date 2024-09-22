-- ///////////////Documentation////////////////////
-- Ethernet interface module implementing the custom
-- ethernet protocol. The module packs transmission
-- requests into valid ethernet frames and parses
-- incoming frames.
-- According to the protocol, only the FPGA is able
-- to establish a connection, so the communication
-- is synchronous and does not require FIFOs.
-- The module only handles specific transmission
-- requests. The logic of combining multiple
-- packets into a complete session is done by the
-- bus handler, which translates high level bus commands
-- into a series of ethernet frames and also intercepts
-- further commands when the interface is busy.
-- Since the length of a frame is usualy flexible, the
-- payload field is read as a byte stream, either
-- from the ether_payload_in port or the module's
-- data_in port.
-- Notice that the gigabit clock is 125MHz, which is
-- exactly half of the system clock. This means the
-- data rate on each stream is 4 bits per clock cycle.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;
use work.ethernet_protocol.all;

entity ethernet_interface is
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(63 downto 0);
        -- data flow ports
        data_in         :   in  std_logic_vector(15 downto 0);
        txd_out         :   out std_logic_vector(3 downto 0); -- RGMII txd
        txctl_out       :   out std_logic; -- RGMII txctl
        txc_out         :   out std_logic; -- RGMII txclk
        rxd_in          :   in  std_logic_vector(3 downto 0); -- RGMII rxd
        rxctl_in        :   in  std_logic;  -- RGMII rxctl
        rxc_in          :   in  std_logic; -- RGMII rxclk
        phy_rst_out     :   out std_logic; -- PHY reset
        -- internal ports connected to the bus handler
        ether_request           :   in  std_logic; -- The controller requests a transmission
        ether_is_transaction    :   in  std_logic; -- Is the request a transaction frame or a data frame
        ether_transaction_type  :   in  ether_word(0 to 0); -- Type of transaction, ignored if data frame
        ether_action_type       :   in  ether_word(0 to 0); -- Type of action, ignored if data frame
        ether_fetch_payload     :   out std_logic; -- Inform the controller to start writing the payload the next cycle
        ether_payload_in        :   in  std_logic_vector(7 downto 0); -- Payload of a transaction frame, 44 bytes
        ether_status            :   out std_logic_vector(3 downto 0); -- Status of the interface
        ether_payload_out       :   out std_logic_vector(7 downto 0); -- Payload of a transaction frame, 44 bytes
        ether_frame_number_in   :   in  std_logic_vector(31 downto 0); -- Frame number requested for data frame
        ether_data_length_in    :   in  std_logic_vector(15 downto 0) -- Length of the data requested for data frame
    );
end entity ethernet_interface;

architecture behaviorial of ethernet_interface is
    type state_type is (s_idle, s_transmit_preamble, s_transmit_destination,
                        s_transmit_source, s_transmit_type, s_transmit_payload,
                        s_transmit_fcs, s_listen, s_receive_preamble, s_receive_destination,
                        s_receive_source, s_receive_type, s_receive_payload, s_receive_fcs,
                        s_success, s_error);
    signal state : state_type := s_idle;

    signal ether_is_transaction_buf : std_logic;
    signal ether_transaction_type_buf : ether_word(0 to 0);
    signal ether_action_type_buf : ether_word(0 to 0);
    signal ether_frame_number_in_buf : std_logic_vector(31 downto 0);
    signal ether_data_length_in_buf : std_logic_vector(15 downto 0);

    signal txd_buf : std_logic_vector(7 downto 0) := (others => '0');

    signal byte_counter : unsigned(15 downto 0) := (others => '0');
    signal cycle_counter : std_logic := '0'; -- 0: send LSB, 1: send MSB of the txd_buf
begin
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= s_idle;
            else
                case state is
                    when s_idle =>
                        if ether_request = '1' then
                            state <= s_transmit_preamble;
                            ether_is_transaction_buf <= ether_is_transaction;
                            if ether_is_transaction = '1' then
                                ether_transaction_type_buf <= ether_transaction_type;
                                ether_action_type_buf <= ether_action_type;
                            else
                                ether_frame_number_in_buf <= ether_frame_number_in;
                                ether_data_length_in_buf <= ether_data_length_in;
                            end if;
                            byte_counter <= (others => '0');
                        end if;
                    when s_transmit_preamble =>
                        
                    when others =>
                        state <= s_idle;
                end case;
            end if;
        end if;
    end process;
end behaviorial;