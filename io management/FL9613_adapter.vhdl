-- ///////////////Documentation////////////////////
-- Maps input data, output clock and spi signals
-- to the universal LPC interface. Contains FIFO logic. 

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Instantiating Kintex Ultrascale primitives
library unisim;
use unisim.vcomponents.all;

use work.mypak.all;

entity FL9613_adapter is
    port(
        adc_a_data      :   out std_logic_vector(15 downto 0);
        adc_b_data      :   out std_logic_vector(15 downto 0);
        adc_c_data      :   out std_logic_vector(15 downto 0);
        adc_d_data      :   out std_logic_vector(15 downto 0);
        adc_spi_ss      :   in  std_logic_vector(0 to 3);
        adc_spi_sck     :   in  std_logic;
        adc_spi_mosi    :   in  std_logic;
        adc_spi_miso    :   out  std_logic;
        adc_spi_io_tri  :   in  std_logic;
        sys_clk         :   in  std_logic;
        adc_clk_250M    :   in std_logic;
        sys_rst         :   in  std_logic;

        adc_a_b_data_fmc : in std_logic_vector(11 downto 0);
        adc_c_d_data_fmc : in std_logic_vector(11 downto 0);
        adc_a_b_dco_fmc : in std_logic;
        adc_c_d_dco_fmc : in std_logic;
        adc_a_b_spi_ss_fmc : out std_logic;
        adc_c_d_spi_ss_fmc : out std_logic;
        adc_clk_spi_ss_fmc : out std_logic;
        adc_spi_sck_fmc : out std_logic;
        adc_spi_mosi_fmc : out std_logic;
        adc_a_b_spi_miso_fmc : in std_logic;
        adc_c_d_spi_miso_fmc : in std_logic;
        adc_clk_spi_miso_fmc : in std_logic;
        adc_spi_io_tri_fmc : out std_logic;
        adc_clk_250M_fmc : out std_logic;
        adc_eeprom_iic_scl_fmc : out std_logic;
        adc_eeprom_iic_sda_fmc : out std_logic
    );
end entity FL9613_adapter;

architecture structural of FL9613_adapter is
    signal sys_rst_adc_a_b_1    : std_logic;
    signal sys_rst_adc_a_b_2    : std_logic;
    signal sys_rst_adc_c_d_1    : std_logic;
    signal sys_rst_adc_c_d_2    : std_logic;

    signal adc_a_data_buf       : std_logic_vector(11 downto 0);
    signal adc_b_data_buf       : std_logic_vector(11 downto 0);
    signal adc_c_data_buf       : std_logic_vector(11 downto 0);
    signal adc_d_data_buf       : std_logic_vector(11 downto 0);
    signal adc_a_b_data_h       : std_logic_vector(11 downto 0);
    signal adc_a_b_data_l       : std_logic_vector(11 downto 0);
    signal adc_c_d_data_h       : std_logic_vector(11 downto 0);
    signal adc_c_d_data_l       : std_logic_vector(11 downto 0);
    signal adc_a_b_data         : std_logic_vector(11 downto 0);
    signal adc_c_d_data         : std_logic_vector(11 downto 0);
    signal adc_a_b_dco          : std_logic;
    signal adc_c_d_dco          : std_logic;
    signal adc_a_b_or           : std_logic;
    signal adc_c_d_or           : std_logic;
    signal adc_clk_reset        : std_logic;
    signal adc_clk_sync         : std_logic;
    signal adc_sync             : std_logic;
    signal adc_trig             : std_logic;
    signal adc_eeprom_iic_scl   : std_logic;
    signal adc_eeprom_iic_sda   : std_logic;

    signal adc_a_data_fifo_rrst_busy    : std_logic;
    signal adc_a_data_fifo_wrst_busy    : std_logic;
    signal adc_a_data_fifo_empty        : std_logic;
    signal adc_a_data_fifo_full         : std_logic;
    signal adc_a_data_fifo_ren          : std_logic;
    signal adc_a_data_fifo_ren_1        : std_logic;
    signal adc_a_data_fifo_wen          : std_logic;
    signal adc_b_data_fifo_rrst_busy    : std_logic;
    signal adc_b_data_fifo_wrst_busy    : std_logic;
    signal adc_b_data_fifo_empty        : std_logic;
    signal adc_b_data_fifo_full         : std_logic;
    signal adc_b_data_fifo_ren          : std_logic;
    signal adc_b_data_fifo_ren_1        : std_logic;
    signal adc_b_data_fifo_wen          : std_logic;
    signal adc_c_data_fifo_rrst_busy    : std_logic;
    signal adc_c_data_fifo_wrst_busy    : std_logic;
    signal adc_c_data_fifo_empty        : std_logic;
    signal adc_c_data_fifo_full         : std_logic;
    signal adc_c_data_fifo_ren          : std_logic;
    signal adc_c_data_fifo_ren_1        : std_logic;
    signal adc_c_data_fifo_wen          : std_logic;
    signal adc_d_data_fifo_rrst_busy    : std_logic;
    signal adc_d_data_fifo_wrst_busy    : std_logic;
    signal adc_d_data_fifo_empty        : std_logic;
    signal adc_d_data_fifo_full         : std_logic;
    signal adc_d_data_fifo_ren          : std_logic;
    signal adc_d_data_fifo_ren_1        : std_logic;
    signal adc_d_data_fifo_wen          : std_logic;

    attribute ASYNC_REG : string;
    attribute ASYNC_REG of sys_rst_adc_a_b_1 : signal is "TRUE";
    attribute ASYNC_REG of sys_rst_adc_a_b_2 : signal is "TRUE";
    attribute ASYNC_REG of sys_rst_adc_c_d_1 : signal is "TRUE";
    attribute ASYNC_REG of sys_rst_adc_c_d_2 : signal is "TRUE";
begin
    -- 1 bit cdc syncronizer for sys_rst
    process(adc_a_b_dco)
    begin
        if rising_edge(adc_a_b_dco) then
            sys_rst_adc_a_b_1 <= sys_rst;
            sys_rst_adc_a_b_2 <= sys_rst_adc_a_b_1;
        end if;
    end process;
    process(adc_c_d_dco)
    begin
        if rising_edge(adc_c_d_dco) then
            sys_rst_adc_c_d_1 <= sys_rst;
            sys_rst_adc_c_d_2 <= sys_rst_adc_c_d_1;
        end if;
    end process;

    -- Interface
    -- Transfer data from slow adc clock to system clock by employing asynchronous fifo
    adc_a_data_fifo : entity work.async_fifo generic map(
        width => 12
    )port map(
        wclk => adc_a_b_dco,
        rclk => sys_clk,
        rst => sys_rst_adc_a_b_2,
        wdata_in => adc_a_b_data_h,
        wen_in => adc_a_data_fifo_wen,
        rdata_out => adc_a_data_buf,
        ren_in => adc_a_data_fifo_ren,
        wrst_busy_out => adc_a_data_fifo_wrst_busy,
        rrst_busy_out => adc_a_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => adc_a_data_fifo_empty,
        wfull_out => adc_a_data_fifo_full,
        rfull_out => open
    );
    adc_a_data_fifo_wen <= not adc_a_data_fifo_full and not adc_a_data_fifo_wrst_busy;
    adc_a_data_fifo_ren <= not adc_a_data_fifo_empty and not adc_a_data_fifo_rrst_busy;
    adc_b_data_fifo : entity work.async_fifo generic map(
        width => 12
    )port map(
        wclk => adc_a_b_dco,
        rclk => sys_clk,
        rst => sys_rst_adc_a_b_2,
        wdata_in => adc_a_b_data_l,
        wen_in => adc_b_data_fifo_wen,
        rdata_out => adc_b_data_buf,
        ren_in => adc_b_data_fifo_ren,
        wrst_busy_out => adc_b_data_fifo_wrst_busy,
        rrst_busy_out => adc_b_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => adc_b_data_fifo_empty,
        wfull_out => adc_b_data_fifo_full,
        rfull_out => open
    );
    adc_b_data_fifo_wen <= not adc_b_data_fifo_full and not adc_b_data_fifo_wrst_busy;
    adc_b_data_fifo_ren <= not adc_b_data_fifo_empty and not adc_b_data_fifo_rrst_busy;
    process(sys_clk)
    begin
        if rising_edge(sys_clk) then
            adc_a_data_fifo_ren_1 <= adc_a_data_fifo_ren;
            adc_b_data_fifo_ren_1 <= adc_b_data_fifo_ren;
            if adc_a_data_fifo_ren_1 = '1' then
                adc_a_data <= adc_a_data_buf & x"0";
            end if;
            if adc_b_data_fifo_ren_1 = '1' then
                adc_b_data <= adc_b_data_buf & x"0";
            end if;
        end if;
    end process;
    adc_c_data_fifo : entity work.async_fifo generic map(
        width => 12
    )port map(
        wclk => adc_c_d_dco,
        rclk => sys_clk,
        rst => sys_rst_adc_c_d_2,
        wdata_in => adc_c_d_data_h,
        wen_in => adc_c_data_fifo_wen,
        rdata_out => adc_c_data_buf,
        ren_in => adc_c_data_fifo_ren,
        wrst_busy_out => adc_c_data_fifo_wrst_busy,
        rrst_busy_out => adc_c_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => adc_c_data_fifo_empty,
        wfull_out => adc_c_data_fifo_full,
        rfull_out => open
    );
    adc_c_data_fifo_wen <= not adc_c_data_fifo_full and not adc_c_data_fifo_wrst_busy;
    adc_c_data_fifo_ren <= not adc_c_data_fifo_empty and not adc_c_data_fifo_rrst_busy;
    adc_d_data_fifo : entity work.async_fifo generic map(
        width => 12
    )port map(
        wclk => adc_c_d_dco,
        rclk => sys_clk,
        rst => sys_rst_adc_c_d_2,
        wdata_in => adc_c_d_data_l,
        wen_in => adc_d_data_fifo_wen,
        rdata_out => adc_d_data_buf,
        ren_in => adc_d_data_fifo_ren,
        wrst_busy_out => adc_d_data_fifo_wrst_busy,
        rrst_busy_out => adc_d_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => adc_d_data_fifo_empty,
        wfull_out => adc_d_data_fifo_full,
        rfull_out => open
    );
    adc_d_data_fifo_wen <= not adc_d_data_fifo_full and not adc_d_data_fifo_wrst_busy;
    adc_d_data_fifo_ren <= not adc_d_data_fifo_empty and not adc_d_data_fifo_rrst_busy;
    process(sys_clk)
    begin
        if rising_edge(sys_clk) then
            adc_c_data_fifo_ren_1 <= adc_c_data_fifo_ren;
            adc_d_data_fifo_ren_1 <= adc_d_data_fifo_ren;
            if adc_c_data_fifo_ren_1 = '1' then
                adc_c_data <= adc_c_data_buf & x"0";
            end if;
            if adc_d_data_fifo_ren_1 = '1' then
                adc_d_data <= adc_d_data_buf & x"0";
            end if;
        end if;
    end process;

    adc_eeprom_iic_scl <= '1'; -- EEPROM part not finished yet
    adc_eeprom_iic_sda <= '0'; -- EEPROM part not finished yet

    -- IDDREs
    adc_a_b_data_iddre1_gen : for i in 0 to 11 generate
        adc_a_b_data_iddre1 : IDDRE1 port map(
            Q1 => adc_a_b_data_h(i),
            Q2 => adc_a_b_data_l(i),
            C => adc_a_b_dco,
            CB => not adc_a_b_dco,
            D => adc_a_b_data(i),
            R => sys_rst_adc_a_b_2
        );
    end generate adc_a_b_data_iddre1_gen;
    adc_c_d_data_iddre1_gen : for i in 0 to 11 generate
        adc_c_d_data_iddre1 : IDDRE1 port map(
            Q1 => adc_c_d_data_h(i),
            Q2 => adc_c_d_data_l(i),
            C => adc_c_d_dco,
            CB => not adc_c_d_dco,
            D => adc_c_d_data(i),
            R => sys_rst_adc_c_d_2
        );
    end generate adc_c_d_data_iddre1_gen;

    adc_a_b_data <= adc_a_b_data_fmc;
    adc_c_d_data <= adc_c_d_data_fmc;
    adc_a_b_dco <= adc_a_b_dco_fmc;
    adc_c_d_dco <= adc_c_d_dco_fmc;
    adc_a_b_spi_ss_fmc <= adc_spi_ss(0);
    adc_c_d_spi_ss_fmc <= adc_spi_ss(1);
    adc_clk_spi_ss_fmc <= adc_spi_ss(2);
    adc_spi_sck_fmc <= adc_spi_sck;
    adc_spi_mosi_fmc <= adc_spi_mosi;
    adc_spi_miso <= adc_a_b_spi_miso_fmc when adc_spi_ss(0) = '0' else
                    adc_c_d_spi_miso_fmc when adc_spi_ss(1) = '0' else
                    adc_clk_spi_miso_fmc when adc_spi_ss(2) = '0' else
                    '0';
    adc_spi_io_tri_fmc <= adc_spi_io_tri;
    adc_clk_250M_fmc <= adc_clk_250M;
    adc_eeprom_iic_scl_fmc <= adc_eeprom_iic_scl;
    adc_eeprom_iic_sda_fmc <= adc_eeprom_iic_sda;
end architecture structural;
        
