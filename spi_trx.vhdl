-- ///////////////Documentation////////////////////
-- Simple SPI transceiver.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity spi_trx is
    generic(
        cpol        :   std_logic := '0'; -- SPI clock polarity
        cpha        :   std_logic := '0' -- SPI clock phase
    );
    port(
        clk         :   in  std_logic; -- Clock
        rst         :   in  std_logic; -- Reset
        spi_en_in   :   in  std_logic; -- SPI enable. Transmission initiated with a high pulse
        ss_in       :   in  std_logic_vector(3 downto 0); -- Slave select input encoded in binary
        ss_out      :   out std_logic_vector(0 to 15); -- Slave select output encoded as one-hot
        mosi        :   out std_logic; -- Master out slave in
        miso        :   in  std_logic; -- Master in slave out
        sclk_out    :   out std_logic; -- SPI clock
        control_in  :   in  std_logic_vector(31 downto 0); -- Control signal, contains parameters for current spi transmission
        io_tri_out  :   out std_logic; -- Tri-state iobuf control for bidirectional wire
        din         :   in  std_logic_vector(31 downto 0); -- Data to be transmitted
        dout        :   out std_logic_vector(31 downto 0); -- Received data
        dval_out    :   out std_logic; -- Data valid indicated with a high pulse
        idle_out    :   out std_logic -- SPI idle
    );
end spi_trx;

architecture behavioral of spi_trx is
    constant clk_period         : unsigned(7 downto 0) := to_unsigned(clk_freq / spi_clk_freq, 8); -- SPI clock period
    constant half_clk_period    : unsigned(7 downto 0) := clk_period / 2; -- Half SPI clock period

    type state_type is (s_idle, s_load, s_transmit, s_end);
    signal state        : state_type := s_idle;

    signal sclk         : std_logic; -- SPI clock
    signal cycle_cnt    : unsigned(7 downto 0); -- Counts for when to flip sclk
    signal bit_cnt      : unsigned(4 downto 0); -- Counts for how many bits have been transmitted
    signal sclk_edge    : std_logic; -- Indicates if sclk is at an edge
    signal sample_edge  : std_logic; -- Indicates if the coming edge is a sample edge

    signal width        : unsigned(4 downto 0); -- Width of the spi transmission. 0-31 represents 1-32 bits
    signal write_count  : unsigned(4 downto 0); -- Counter for write bits. 0-31 represents 1-32 bits
    -- Used for some spi transmissions that requires a bidirectional wire, where the state of iobuffer must be controlled
    
    signal sr           : std_logic_vector(31 downto 0); -- Shift register, MSB first
    signal sr_din       : std_logic; -- Bit in
begin
    -- FSM
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= s_idle;
            else
                case state is
                    when s_idle =>
                        if spi_en_in = '1' then
                            state <= s_load;
                        end if;
                    when s_load =>
                        state <= s_transmit;
                    when s_transmit =>
                        if sclk_edge = '1' and bit_cnt = "00000" and sclk /= cpol then
                            state <= s_end;
                        end if;
                    when s_end =>
                        if sclk_edge = '1' then
                            state <= s_idle;
                        end if;
                end case;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_transmit and sclk_edge = '1' and sample_edge = '1' then
                sr_din <= miso;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_end and sclk_edge = '1' then
                dval_out <= '1';
            else
                dval_out <= '0';
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if (state = s_transmit or state = s_end) and sclk_edge = '0' then
                cycle_cnt <= cycle_cnt + x"01";
            else
                cycle_cnt <= (others => '0');
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_transmit then
                if sclk_edge = '1' and sclk = cpol then
                    if bit_cnt = width then
                        bit_cnt <= "00000";
                    else
                        bit_cnt <= bit_cnt + "00001";
                    end if;
                end if;
            else
                bit_cnt <= "00000";
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_transmit then
                if sclk_edge = '1' then
                    sclk <= not sclk;
                end if;
            else
                sclk <= cpol;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_transmit then
                if sclk_edge = '1' and sample_edge = '0' and bit_cnt = write_count + "00001" then
                    io_tri_out <= '1';
                end if;
            else
                io_tri_out <= '0';
            end if;
        end if;
    end process;
    
    -- Shift register
    process(clk)
    begin
        if rising_edge(clk) then
            case state is
                when s_load =>
                    sr <= din;
                when s_transmit =>
                    if sclk_edge = '1' and sample_edge = '0' and bit_cnt /= "00000" then
                        sr <= sr(30 downto 0) & sr_din;
                    end if;
                when s_end =>
                    if sclk_edge = '1' then
                        sr <= sr(30 downto 0) & sr_din;
                    end if;
                when others =>
            end case;
        end if;
    end process;

    sclk_edge <= '1' when cycle_cnt = half_clk_period + x"FF" else '0';
    sample_edge <= not cpol xor cpha xor sclk;

    mosi <= sr(31);
    dout <= sr;
    sclk_out <= sclk;
    idle_out <= '1' when state = s_idle else '0';

    width <= unsigned(control_in(4 downto 0));
    write_count <= unsigned(control_in(12 downto 8));

    -- ss binary to one-hot conversion
    one_hot : for i in 0 to 15 generate
        ss_out(i) <= '0' when ss_in = std_logic_vector(to_unsigned(i, 4)) and state /= s_idle else '1';
    end generate;
end behavioral;