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
        rsp_sel_out     :   out std_logic_vector(mbus_w - 1 downto 0);
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
    type state_type is (idle, hold, receive, transmit, error);
    signal state    :   state_type := idle;
    signal byte     :   std_logic_vector(7 downto 0);

    signal cnt      :   unsigned(2 downto 0) := (others => '0');
begin
    process(clk, rst)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                rxen_out <= '0';
                txen_out <= '0';
                byte <= (others => '0');
                txd_out <= (others => '0');
                state <= idle;
            else
                case state is
                    when idle =>
                        txen_out <= '0';
                        if rxemp_in = '0' then
                            rxen_out <= '1';
                            state <= hold;
                        end if;
                    when hold =>
                        rxen_out <= '0';
                        state <= receive;
                    when receive =>
                        byte <= rxd_in;
                        if txful_in = '0' then
                            state <= transmit;
                        else
                            state <= error;
                        end if;
                    when transmit =>
                        txen_out <= '1';
                        txd_out <= byte;
                        state <= idle;
                    when error =>
                        -- Do nothing
                end case;
            end if;
        end if;
    end process;
    
    process(clk)
    begin
        if rising_edge(clk) then
            if state = transmit then
                cnt <= cnt + "001";
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            case cnt is
                when "000" =>
                    dbus_out(7 downto 0) <= byte;
                when "001" =>
                    dbus_out(15 downto 8) <= byte;
                when "010" =>
                    dbus_out(23 downto 16) <= byte;
                when "011" =>
                    dbus_out(31 downto 24) <= byte;
                when "100" =>
                    abus_out <= byte(4 downto 0);
                when "101" =>
                    mbus_out <= byte(4 downto 0);
                when "110" =>
                    cbus_out <= byte(4 downto 0);
                when "111" =>
                    rsp_sel_out <= byte(4 downto 0);
                when others =>
            end case;
        end if;
    end process;
end architecture repeater;