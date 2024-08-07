-- ///////////////Documentation////////////////////
-- Adapt the io ports to fit the hardware.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Instantiating Kintex Ultrascale primitives
library unisim;
use unisim.vcomponents.all;

use work.mypak.all;

entity wrapper is
    port(
        sys_clk_p       :   in  std_logic;
        sys_clk_n       :   in  std_logic;
        rst             :   in  std_logic;

        -- LED lights
        led_1_o         :   out std_logic;
        led_2_o         :   out std_logic;
        led_3_o         :   out std_logic;
        led_4_o         :   out std_logic;
        panel_led_1_o   :   out std_logic;
        panel_led_2_o   :   out std_logic;

        -- To serial port
        uart_txd_o      :   out std_logic;
        uart_rxd_i      :   in  std_logic;

        -- To FL9781
        dac_a_b_dci_p_ddr_o     :   out std_logic;
        dac_a_b_dci_n_ddr_o     :   out std_logic;
        dac_a_b_dco_p_i         :   in  std_logic;
        dac_a_b_dco_n_i         :   in  std_logic;
        dac_a_b_data_p_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_a_b_data_n_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_a_b_spi_ss_o        :   out std_logic;
        dac_c_d_dci_p_ddr_o     :   out std_logic;
        dac_c_d_dci_n_ddr_o     :   out std_logic;
        dac_c_d_dco_p_i         :   in  std_logic;
        dac_c_d_dco_n_i         :   in  std_logic;
        dac_c_d_data_p_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_c_d_data_n_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_c_d_spi_ss_o        :   out std_logic;
        dac_clk_spi_ss_o        :   out std_logic;
        dac_spi_sck_o           :   out std_logic;
        dac_spi_mosi_o          :   out std_logic;
        dac_spi_miso_i          :   in  std_logic;
        dac_eeprom_iic_scl_o    :   out std_logic;
        dac_eeprom_iic_sda_io   :   inout std_logic
    );
end entity wrapper;

architecture peripheral_wrapper of wrapper is
    signal sys_clk : std_logic;
    signal sys_clk_buf : std_logic;
    signal sys_rst : std_logic;
    signal sys_rst_bar : std_logic;

    signal led_1 : std_logic;
    signal led_2 : std_logic;
    signal led_3 : std_logic;
    signal led_4 : std_logic;
    signal panel_led_1 : std_logic;
    signal panel_led_2 : std_logic;

    signal uart_txd : std_logic;
    signal uart_rxd : std_logic;

    -- To register an spi module:
    -- 1.Follow the format below, connecting mosi, miso, sclk and one bit from ss to the module
    -- 2.Register the address of the module in mypak
    -- 3.Register the name of the module in uart_protocol
    -- 4.Add corresponding lines in central_control
    signal spi_mosi : std_logic;
    signal spi_miso : std_logic;
    signal spi_sclk : std_logic;
    signal spi_ss   : std_logic_vector(15 downto 0);

    signal dac_a_b_data_h_buf : std_logic_vector(13 downto 0);
    signal dac_a_b_data_l_buf : std_logic_vector(13 downto 0);
    signal dac_c_d_data_h_buf : std_logic_vector(13 downto 0);
    signal dac_c_d_data_l_buf : std_logic_vector(13 downto 0);
    signal dac_a_b_data_h : std_logic_vector(13 downto 0);
    signal dac_a_b_data_l : std_logic_vector(13 downto 0);
    signal dac_c_d_data_h : std_logic_vector(13 downto 0);
    signal dac_c_d_data_l : std_logic_vector(13 downto 0);
    signal dac_a_b_data : std_logic_vector(13 downto 0);
    signal dac_c_d_data : std_logic_vector(13 downto 0);
    signal dac_a_b_dci_h : std_logic;
    signal dac_a_b_dci_l : std_logic;
    signal dac_c_d_dci_h : std_logic;
    signal dac_c_d_dci_l : std_logic;
    signal dac_a_b_dci : std_logic;
    signal dac_c_d_dci : std_logic;
    signal dac_a_b_dco : std_logic;
    signal dac_a_b_dco_buf : std_logic;
    signal dac_c_d_dco : std_logic;
    signal dac_c_d_dco_buf : std_logic;
    signal dac_a_b_spi_ss : std_logic;
    signal dac_c_d_spi_ss : std_logic;
    signal dac_clk_spi_ss : std_logic;
    signal dac_spi_sck : std_logic;
    signal dac_spi_mosi : std_logic;
    signal dac_spi_miso : std_logic;
    signal dac_eeprom_iic_scl : std_logic;
    signal dac_eeprom_iic_sda : std_logic;

    signal dac_a_data_buf : std_logic_vector(13 downto 0);
    signal dac_b_data_buf : std_logic_vector(13 downto 0);
    signal dac_c_data_buf : std_logic_vector(13 downto 0);
    signal dac_d_data_buf : std_logic_vector(13 downto 0);

    signal dac_a_data_fifo_rst_busy : std_logic;
    signal dac_a_data_fifo_empty : std_logic;
    signal dac_a_data_fifo_ren : std_logic;
    signal dac_a_data_fifo_ren_1 : std_logic;
    signal dac_b_data_fifo_rst_busy : std_logic;
    signal dac_b_data_fifo_empty : std_logic;
    signal dac_b_data_fifo_ren : std_logic;
    signal dac_b_data_fifo_ren_1 : std_logic;
    signal dac_c_data_fifo_rst_busy : std_logic;
    signal dac_c_data_fifo_empty : std_logic;
    signal dac_c_data_fifo_ren : std_logic;
    signal dac_c_data_fifo_ren_1 : std_logic;
    signal dac_d_data_fifo_rst_busy : std_logic;
    signal dac_d_data_fifo_empty : std_logic;
    signal dac_d_data_fifo_ren : std_logic;
    signal dac_d_data_fifo_ren_1 : std_logic;
begin
    top : entity work.top port map(
        clk => sys_clk,
        rst => sys_rst_bar,
        txd => uart_txd,
        rxd => uart_rxd,

        mosi => spi_mosi,
        miso => spi_miso,
        sclk => spi_sclk,
        ss => spi_ss,

        -- adc not connected to physical ports yet
        adc_in_a => (others => '0'),
        adc_in_b => (others => '0'),
        adc_in_c => (others => '0'),
        adc_in_d => (others => '0'),

        dac_out_a => dac_a_data_buf,
        dac_out_b => dac_b_data_buf,
        dac_out_c => dac_c_data_buf,
        dac_out_d => dac_d_data_buf
    );

    -- Multiplexing SPI miso signals
    -- Using dac_spi_miso when spi_ss is selecting chips on the dac module
    spi_miso <= dac_spi_miso when spi_ss(SPI_DAC1_ADDR) = '0' or spi_ss(SPI_DAC2_ADDR) = '0' or spi_ss(SPI_CLK1_ADDR) = '0' else '0';

    -- leds
    led_1 <= not uart_rxd; -- detects input bit flow
    led_2 <= not uart_txd; -- detects output bit flow
    led_3 <= spi_sclk; -- detects spi clock
    led_4 <= not (and spi_ss); -- detects if any spi chip is selected
    panel_led_1 <= '1'; -- detects if the system is running
    panel_led_2 <= sys_rst_bar; -- detects if the system is reset

    -- Interface to FL9781
    -- Align data transferred with lvds data clock
    -- Transfer data from slow system clock to fast dac clock by employing asynchronous fifo
    -- Read latency is known to be 1 cycle, so don't care valid signal
    dac_a_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => dac_a_b_dco,
        rst => sys_rst_bar,
        wdata_in => dac_a_data_buf,
        wen_in => not dac_a_data_fifo_rst_busy,
        rdata_out => dac_a_b_data_h_buf,
        ren_in => dac_a_data_fifo_ren,
        rval_out => open,
        rst_busy_out => dac_a_data_fifo_rst_busy,
        empty_out => dac_a_data_fifo_empty
    );
    -- Period ratio is approximately 2:5, so skip each other cycle to flatten the data rate
    -- Thus deassert the read enable signal when ren stage 1 register is high
    dac_a_data_fifo_ren <= not dac_a_data_fifo_empty and not dac_a_data_fifo_rst_busy and not dac_a_data_fifo_ren_1;
    dac_b_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => dac_a_b_dco,
        rst => sys_rst_bar,
        wdata_in => dac_b_data_buf,
        wen_in => not dac_b_data_fifo_rst_busy,
        rdata_out => dac_a_b_data_l_buf,
        ren_in => dac_b_data_fifo_ren,
        rval_out => open,
        rst_busy_out => dac_b_data_fifo_rst_busy,
        empty_out => dac_b_data_fifo_empty
    );
    dac_b_data_fifo_ren <= not dac_b_data_fifo_empty and not dac_b_data_fifo_rst_busy and not dac_b_data_fifo_ren_1;
    process(dac_a_b_dco)
    begin
        if rising_edge(dac_a_b_dco) then
            dac_a_data_fifo_ren_1 <= dac_a_data_fifo_ren;
            dac_b_data_fifo_ren_1 <= dac_b_data_fifo_ren;
            if dac_a_data_fifo_ren_1 = '1' then
                dac_a_b_data_h <= dac_a_b_data_h_buf;
            end if;
            if dac_b_data_fifo_ren_1 = '1' then
                dac_a_b_data_l <= dac_a_b_data_l_buf;
            end if;
        end if;
    end process;
    dac_c_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => dac_c_d_dco,
        rst => sys_rst_bar,
        wdata_in => dac_c_data_buf,
        wen_in => not dac_c_data_fifo_rst_busy,
        rdata_out => dac_c_d_data_h_buf,
        ren_in => dac_c_data_fifo_ren,
        rval_out => open,
        rst_busy_out => dac_c_data_fifo_rst_busy,
        empty_out => dac_c_data_fifo_empty
    );
    dac_c_data_fifo_ren <= not dac_c_data_fifo_empty and not dac_c_data_fifo_rst_busy and not dac_c_data_fifo_ren_1;
    dac_d_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => dac_c_d_dco,
        rst => sys_rst_bar,
        wdata_in => dac_d_data_buf,
        wen_in => not dac_d_data_fifo_rst_busy,
        rdata_out => dac_c_d_data_l_buf,
        ren_in => dac_d_data_fifo_ren,
        rval_out => open,
        rst_busy_out => dac_d_data_fifo_rst_busy,
        empty_out => dac_d_data_fifo_empty
    );
    dac_d_data_fifo_ren <= not dac_d_data_fifo_empty and not dac_d_data_fifo_rst_busy and not dac_d_data_fifo_ren_1;
    process(dac_c_d_dco)
    begin
        if rising_edge(dac_c_d_dco) then
            dac_c_data_fifo_ren_1 <= dac_c_data_fifo_ren;
            dac_d_data_fifo_ren_1 <= dac_d_data_fifo_ren;
            if dac_c_data_fifo_ren_1 = '1' then
                dac_c_d_data_h <= dac_c_d_data_h_buf;
            end if;
            if dac_d_data_fifo_ren_1 = '1' then
                dac_c_d_data_l <= dac_c_d_data_l_buf;
            end if;
        end if;
    end process;

    dac_a_b_dci_h <= '1';
    dac_a_b_dci_l <= '0';
    dac_c_d_dci_h <= '1';
    dac_c_d_dci_l <= '0';
    dac_a_b_spi_ss <= spi_ss(SPI_DAC1_ADDR);
    dac_c_d_spi_ss <= spi_ss(SPI_DAC2_ADDR);
    dac_clk_spi_ss <= spi_ss(SPI_CLK1_ADDR);
    dac_spi_sck <= spi_sclk;
    dac_spi_mosi <= spi_mosi;
    dac_eeprom_iic_scl <= '1'; -- EEPROM part not finished yet
    dac_eeprom_iic_sda <= '0'; -- EEPROM part not finished yet



    -- IO buffers
    -- clk
    sys_clk_ibufds : IBUFDS port map(
        O => sys_clk_buf,
        I => sys_clk_p,
        IB => sys_clk_n
    );
    sys_clk_bufg : BUFG port map(
        O => sys_clk,
        I => sys_clk_buf
    );

    --rst
    sys_rst_ibuf : IBUF port map(
        O => sys_rst,
        I => rst
    );
    sys_rst_bar <= not sys_rst;

    -- leds
    led_1_obuf : OBUF port map(
        O => led_1_o,
        I => led_1
    );
    led_2_obuf : OBUF port map(
        O => led_2_o,
        I => led_2
    );
    led_3_obuf : OBUF port map(
        O => led_3_o,
        I => led_3
    );
    led_4_obuf : OBUF port map(
        O => led_4_o,
        I => led_4
    );
    panel_led_1_obuf : OBUF port map(
        O => panel_led_1_o,
        I => panel_led_1
    );
    panel_led_2_obuf : OBUF port map(
        O => panel_led_2_o,
        I => panel_led_2
    );

    -- FL9781, using dco returned from the chip to clock out data
    dac_a_b_dci_oddre1 : ODDRE1 port map(
        Q => dac_a_b_dci,
        C => dac_a_b_dco,
        D1 => dac_a_b_dci_h,
        D2 => dac_a_b_dci_l,
        SR => sys_rst_bar
    );
    dac_a_b_dci_obufds : OBUFDS port map(
        O => dac_a_b_dci_p_ddr_o,
        OB => dac_a_b_dci_n_ddr_o,
        I => dac_a_b_dci
    );
    dac_a_b_data_oddre1_gen : for i in 0 to 13 generate
        dac_a_b_data_oddre1 : ODDRE1 port map(
            Q => dac_a_b_data(i),
            C => dac_a_b_dco,
            D1 => dac_a_b_data_h(i),
            D2 => dac_a_b_data_l(i),
            SR => sys_rst_bar
        );
    end generate dac_a_b_data_oddre1_gen;
    dac_a_b_data_obufds_gen : for i in 0 to 13 generate
        dac_a_b_data_obufds : OBUFDS port map(
            O => dac_a_b_data_p_ddr_o(i),
            OB => dac_a_b_data_n_ddr_o(i),
            I => dac_a_b_data(i)
        );
    end generate dac_a_b_data_obufds_gen;
    dac_c_d_dci_oddre1 : ODDRE1 port map(
        Q => dac_c_d_dci,
        C => dac_c_d_dco,
        D1 => dac_c_d_dci_h,
        D2 => dac_c_d_dci_l,
        SR => sys_rst_bar
    );
    dac_c_d_dci_obufds : OBUFDS port map(
        O => dac_c_d_dci_p_ddr_o,
        OB => dac_c_d_dci_n_ddr_o,
        I => dac_c_d_dci
    );
    dac_c_d_data_oddre1_gen : for i in 0 to 13 generate
        dac_c_d_data_oddre1 : ODDRE1 port map(
            Q => dac_c_d_data(i),
            C => dac_c_d_dco,
            D1 => dac_c_d_data_h(i),
            D2 => dac_c_d_data_l(i),
            SR => sys_rst_bar
        );
    end generate dac_c_d_data_oddre1_gen;
    dac_c_d_data_obufds_gen : for i in 0 to 13 generate
        dac_c_d_data_obufds : OBUFDS port map(
            O => dac_c_d_data_p_ddr_o(i),
            OB => dac_c_d_data_n_ddr_o(i),
            I => dac_c_d_data(i)
        );
    end generate dac_c_d_data_obufds_gen;
    dac_a_b_spi_ss_obuf : OBUF port map(
        O => dac_a_b_spi_ss_o,
        I => dac_a_b_spi_ss
    );
    dac_c_d_spi_ss_obuf : OBUF port map(
        O => dac_c_d_spi_ss_o,
        I => dac_c_d_spi_ss
    );
    dac_clk_spi_ss_obuf : OBUF port map(
        O => dac_clk_spi_ss_o,
        I => dac_clk_spi_ss
    );
    dac_spi_sck_obuf : OBUF port map(
        O => dac_spi_sck_o,
        I => dac_spi_sck
    );
    dac_spi_mosi_obuf : OBUF port map(
        O => dac_spi_mosi_o,
        I => dac_spi_mosi
    );
    dac_eeprom_iic_scl_obuf : OBUF port map(
        O => dac_eeprom_iic_scl_o,
        I => dac_eeprom_iic_scl
    );
    dac_a_b_dco_ibufds : IBUFDS port map(
        O => dac_a_b_dco_buf,
        I => dac_a_b_dco_p_i,
        IB => dac_a_b_dco_n_i
    );
    dac_a_b_dco_bufg : BUFG port map(
        O => dac_a_b_dco,
        I => dac_a_b_dco_buf
    );
    dac_c_d_dco_ibufds : IBUFDS port map(
        O => dac_c_d_dco_buf,
        I => dac_c_d_dco_p_i,
        IB => dac_c_d_dco_n_i
    );
    dac_c_d_dco_bufg : BUFG port map(
        O => dac_c_d_dco,
        I => dac_c_d_dco_buf
    );
    dac_spi_miso_ibuf : IBUF port map(
        O => dac_spi_miso,
        I => dac_spi_miso_i
    );
    -- replace this with a bidirectional buffer in the future
    dac_eeprom_iic_sda_obuf : OBUF port map(
        O => dac_eeprom_iic_sda_io,
        I => dac_eeprom_iic_sda
    );
    
    -- UART
    uart_txd_obuf : OBUF port map(
        O => uart_txd_o,
        I => uart_txd
    );
    uart_rxd_ibuf : IBUF port map(
        O => uart_rxd,
        I => uart_rxd_i
    );
end architecture peripheral_wrapper;