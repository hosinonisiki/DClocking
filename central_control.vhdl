-- ///////////////Documentation////////////////////
-- This is the central control entity of the system.
-- It processes all input and output data from/to
-- fifo buffers, and communicates with all other
-- modules through buses.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity central_control is
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        rxd_in          :   in  std_logic_vector(7 downto 0);
        rxen_out        :   out std_logic;
        rxemp_in        :   in  std_logic;
        txd_out         :   out std_logic_vector(7 downto 0);
        txen_out        :   out std_logic;
        txful_in        :   in  std_logic;
        rsp_in          :   in  std_logic_vector(rbus_w - 1 downto 0);
        rsp_stat_in     :   in  std_logic_vector(sbus_w - 1 downto 0);
        dbus_out        :   out std_logic_vector(dbus_w - 1 downto 0);
        abus_out        :   out std_logic_vector(abus_w - 1 downto 0);
        mbus_out        :   out std_logic_vector(mbus_w - 1 downto 0);
        cbus_out        :   out std_logic_vector(cbus_w - 1 downto 0)
    );
end entity central_control;

-- This is a simple architecture that repeats any byte received.
-- It is used for testing purposes.
architecture repeater of central_control is
    type state_type is (idle, receive, transmit, error);
    signal state    :   state_type := idle;
    signal byte     :   std_logic_vector(7 downto 0);
begin
    process(clk, rst)
    begin
        if rst = '1' then
            rxen_out <= '0';
            txen_out <= '0';
        elsif rising_edge(clk) then
            case state is
                when idle =>
                    txen_out <= '0';
                    if rxemp_in = '0' then
                        rxen_out <= '1';
                        state <= receive;
                    end if;
                when receive =>
                    rxen_out <= '0';
                    byte <= rxd_in;
                    state <= transmit;
                when transmit =>
                    txen_out <= '1';
                    txd_out <= byte;
                    if txful_in = '0' then
                        state <= idle;
                    else
                        state <= error;
                    end if;
                when error =>
                    -- Do nothing
            end case;
        end if;
    end process;

    -- Unused ports
    dbus_out <= (others => '0');
    abus_out <= (others => '0');
    mbus_out <= (others => '0');
    cbus_out <= (others => '0');
end architecture repeater;