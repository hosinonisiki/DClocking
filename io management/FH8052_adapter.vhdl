-- ///////////////Documentation////////////////////
-- Maps several io signals along with spi signals
-- to the universal LPC interface. Contains FIFO logic. 

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library xpm;
use xpm.vcomponents.all;

use work.mypak.all;

entity FH8052_adapter is
    port (
        sys_clk_250M    :   in  std_logic;
        sys_clk_125M    :   in  std_logic;
        sys_rst         :   in  std_logic;
        adc_a_data      :   out std_logic_vector(15 downto 0);
        adc_b_data      :   out std_logic_vector(15 downto 0);
        dac_a_data      :   in  std_logic_vector(15 downto 0);
        dac_b_data      :   in  std_logic_vector(15 downto 0);
        spi_ss          :   in  std_logic_vector(0 to 3);
        spi_sck         :   in  std_logic;
        spi_mosi        :   in  std_logic;
        spi_miso        :   out std_logic;
        spi_io_tri      :   in  std_logic;
        ref_clk_p       :   out std_logic;
        ref_clk_n       :   out std_logic;
        
        -- fmc ports
        tx_ref_clk_p_fmc    :   in  std_logic;
        tx_ref_clk_n_fmc    :   in  std_logic;
        rx_ref_clk_p_fmc    :   in  std_logic;
        rx_ref_clk_n_fmc    :   in  std_logic;
        tx_sysref_fmc       :   in  std_logic;
        rx_sysref_fmc       :   in  std_logic;
        tx_sync_fmc         :   in  std_logic;
        rx_sync_fmc         :   out std_logic;
        txp_out_fmc         :   out std_logic_vector(3 downto 0);
        txn_out_fmc         :   out std_logic_vector(3 downto 0);
        rxp_in_fmc          :   in  std_logic_vector(3 downto 0);
        rxn_in_fmc          :   in  std_logic_vector(3 downto 0);
        tx_core_clk_p_fmc   :   in  std_logic;
        tx_core_clk_n_fmc   :   in  std_logic;
        rx_core_clk_p_fmc   :   in  std_logic;
        rx_core_clk_n_fmc   :   in  std_logic;
        adc_spi_ss_fmc      :   out std_logic;
        dac_spi_ss_fmc      :   out std_logic;
        clk_spi_ss_fmc      :   out std_logic;
        spi_sck_fmc         :   out std_logic;
        spi_mosi_fmc        :   out std_logic;
        adc_spi_miso_fmc    :   in  std_logic;
        dac_spi_miso_fmc    :   in  std_logic;
        clk_spi_miso_fmc    :   in  std_logic;
        spi_io_tri_fmc      :   out std_logic;
        adc_fda_fmc         :   in  std_logic;
        adc_fdb_fmc         :   in  std_logic;
        adc_pwdn_fmc        :   out std_logic;
        dac_irq_fmc         :   in  std_logic;
        dac_rstn_fmc        :   out std_logic;
        dac_txen_fmc        :   out std_logic;
        clk_status_fmc      :   in  std_logic_vector(0 to 1);
        eeprom_iic_scl_fmc  :   out std_logic;
        eeprom_iic_sda_fmc  :   out std_logic
    );
end entity FH8052_adapter;

architecture structural of FH8052_adapter is
    signal core_rst_1           : std_logic;
    signal core_rst_2           : std_logic;

    signal tx_core_clk          : std_logic_vector(0 to 0);
    signal rx_core_clk          : std_logic_vector(0 to 0);
    signal tx_rst_1             : std_logic;
    signal tx_rst_2             : std_logic;
    signal rx_rst_1             : std_logic;
    signal rx_rst_2             : std_logic;
    signal s_axis_tx_tdata      : std_logic_vector(127 downto 0);
    signal s_axis_tx_tready     : std_logic;
    signal m_axis_rx_tdata      : std_logic_vector(127 downto 0);
    signal m_axis_rx_tvalid     : std_logic;

    signal adc_a_data_buf_0     : std_logic_vector(15 downto 0);
    signal adc_b_data_buf_0     : std_logic_vector(15 downto 0);
    signal adc_a_data_buf_1     : std_logic_vector(15 downto 0);
    signal adc_b_data_buf_1     : std_logic_vector(15 downto 0);
    signal adc_dvalid           : std_logic;

    signal dac_a_data_buf_0     : std_logic_vector(15 downto 0);
    signal dac_b_data_buf_0     : std_logic_vector(15 downto 0);
    signal dac_a_data_buf_1     : std_logic_vector(15 downto 0);
    signal dac_b_data_buf_1     : std_logic_vector(15 downto 0);

    signal adc_a_data_fifo_wen  : std_logic;
    signal adc_a_data_fifo_ren  : std_logic;
    signal adc_a_data_fifo_ren_1 : std_logic;
    signal adc_a_data_fifo_wrst_busy : std_logic;
    signal adc_a_data_fifo_rrst_busy : std_logic;
    signal adc_a_data_fifo_empty : std_logic;
    signal adc_a_data_fifo_full  : std_logic;

    signal adc_b_data_fifo_wen  : std_logic;
    signal adc_b_data_fifo_ren  : std_logic;
    signal adc_b_data_fifo_ren_1 : std_logic;
    signal adc_b_data_fifo_wrst_busy : std_logic;
    signal adc_b_data_fifo_rrst_busy : std_logic;
    signal adc_b_data_fifo_empty : std_logic;
    signal adc_b_data_fifo_full  : std_logic;

    signal dac_a_data_fifo_wen  : std_logic;
    signal dac_a_data_fifo_ren  : std_logic;
    signal dac_a_data_fifo_ren_1 : std_logic;
    signal dac_a_data_fifo_wrst_busy : std_logic;
    signal dac_a_data_fifo_rrst_busy : std_logic;
    signal dac_a_data_fifo_empty : std_logic;
    signal dac_a_data_fifo_full  : std_logic;

    signal dac_b_data_fifo_wen  : std_logic;
    signal dac_b_data_fifo_ren  : std_logic;
    signal dac_b_data_fifo_ren_1 : std_logic;
    signal dac_b_data_fifo_wrst_busy : std_logic;
    signal dac_b_data_fifo_rrst_busy : std_logic;
    signal dac_b_data_fifo_empty : std_logic;
    signal dac_b_data_fifo_full  : std_logic;

    component PZ8052_adapter_bd is
        port (
            sys_clk_125M : in STD_LOGIC;
            tx_ref_clk_p : in STD_LOGIC;
            tx_ref_clk_n : in STD_LOGIC;
            rx_ref_clk_p : in STD_LOGIC;
            rx_ref_clk_n : in STD_LOGIC;
            tx_core_clk : out STD_LOGIC_VECTOR ( 0 to 0 );
            rx_core_clk : out STD_LOGIC_VECTOR ( 0 to 0 );
            tx_core_reset : in STD_LOGIC;
            rx_core_reset : in STD_LOGIC;
            tx_phy_reset : in STD_LOGIC;
            rx_phy_reset : in STD_LOGIC;
            tx_sysref : in STD_LOGIC;
            rx_sysref : in STD_LOGIC;
            tx_sync : in STD_LOGIC;
            rx_sync : out STD_LOGIC;
            s_axis_tx_0_tdata : in STD_LOGIC_VECTOR ( 127 downto 0 );
            s_axis_tx_0_tready : out STD_LOGIC;
            m_axis_rx_0_tdata : out STD_LOGIC_VECTOR ( 127 downto 0 );
            m_axis_rx_0_tvalid : out STD_LOGIC;
            rxp_in_0 : in STD_LOGIC_VECTOR ( 3 downto 0 );
            txp_out_0 : out STD_LOGIC_VECTOR ( 3 downto 0 );
            txn_out_0 : out STD_LOGIC_VECTOR ( 3 downto 0 );
            rxn_in_0 : in STD_LOGIC_VECTOR ( 3 downto 0 );
            rx_aresetn_0 : out STD_LOGIC;
            tx_aresetn_0 : out STD_LOGIC
        );
    end component PZ8052_adapter_bd;

    attribute ASYNC_REG : string;
    attribute ASYNC_REG of tx_rst_1 : signal is "TRUE";
    attribute ASYNC_REG of tx_rst_2 : signal is "TRUE";
    attribute ASYNC_REG of rx_rst_1 : signal is "TRUE";
    attribute ASYNC_REG of rx_rst_2 : signal is "TRUE";
begin
    -- 1 bit cdc synchronizer for sys_rst
    process(sys_clk_125M)
    begin
        if rising_edge(sys_clk_125M) then
            core_rst_1 <= sys_rst;
            core_rst_2 <= core_rst_1;
        end if;
    end process;

    process(tx_core_clk(0))
    begin
        if rising_edge(tx_core_clk(0)) then
            tx_rst_1 <= sys_rst;
            tx_rst_2 <= tx_rst_1;
        end if;
    end process;

    process(rx_core_clk(0))
    begin
        if rising_edge(rx_core_clk(0)) then
            rx_rst_1 <= sys_rst;
            rx_rst_2 <= rx_rst_1;
        end if;
    end process;

    PZ8052_adapter_bd_inst : PZ8052_adapter_bd port map( -- Was a typo, migrate bd to FH8052 later
        sys_clk_125M => sys_clk_125M,
        tx_ref_clk_p => tx_ref_clk_p_fmc,
        tx_ref_clk_n => tx_ref_clk_n_fmc,
        rx_ref_clk_p => rx_ref_clk_p_fmc,
        rx_ref_clk_n => rx_ref_clk_n_fmc,
        tx_core_clk => tx_core_clk,
        rx_core_clk => rx_core_clk,
        tx_core_reset => core_rst_2,
        rx_core_reset => core_rst_2,
        tx_phy_reset => core_rst_2,
        rx_phy_reset => core_rst_2,
        tx_sysref => tx_sysref_fmc,
        rx_sysref => rx_sysref_fmc,
        tx_sync => tx_sync_fmc,
        rx_sync => rx_sync_fmc,
        s_axis_tx_0_tdata => s_axis_tx_tdata,
        s_axis_tx_0_tready => s_axis_tx_tready,
        m_axis_rx_0_tdata => m_axis_rx_tdata,
        m_axis_rx_0_tvalid => m_axis_rx_tvalid,
        rxp_in_0 => rxp_in_fmc,
        rxn_in_0 => rxn_in_fmc,
        txp_out_0 => txp_out_fmc,
        txn_out_0 => txn_out_fmc,
        rx_aresetn_0 => open,
        tx_aresetn_0 => open
    );

    adc_axis_rx_inst : entity work.adc_axis_rx port map(
        clk => rx_core_clk(0),
        rst => rx_rst_2,
        rx_tdata_in => m_axis_rx_tdata,
        rx_tvalid_in => m_axis_rx_tvalid,
        data_a_out => adc_a_data_buf_0,
        data_a_0_out => open,
        data_a_1_out => open,
        data_a_2_out => open,
        data_a_3_out => open,
        data_b_out => adc_b_data_buf_0,
        data_b_0_out => open,
        data_b_1_out => open,
        data_b_2_out => open,
        data_b_3_out => open,
        data_valid_out => adc_dvalid
    );

    dac_axis_tx_inst : entity work.dac_axi_tx port map(
        clk => tx_core_clk(0),
        rst => tx_rst_2,
        tx_tdata_out => s_axis_tx_tdata,
        tx_tready_in => s_axis_tx_tready,
        data_a_in => dac_a_data_buf_0,
        data_b_in => dac_b_data_buf_0
    );

    -- CDCs
    adc_a_data_fifo : entity work.async_fifo generic map(
        width => 16
    )port map(
        wclk => rx_core_clk(0),
        rclk => sys_clk_250M,
        rst => rx_rst_2,
        wdata_in => adc_a_data_buf_0,
        wen_in => adc_a_data_fifo_wen,
        rdata_out => adc_a_data_buf_1,
        ren_in => adc_a_data_fifo_ren,
        wrst_busy_out => adc_a_data_fifo_wrst_busy,
        rrst_busy_out => adc_a_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => adc_a_data_fifo_empty,
        wfull_out => adc_a_data_fifo_full,
        rfull_out => open
    );
    adc_a_data_fifo_wen <= not adc_a_data_fifo_full and not adc_a_data_fifo_wrst_busy and adc_dvalid;
    adc_a_data_fifo_ren <= not adc_a_data_fifo_empty and not adc_a_data_fifo_rrst_busy;
    adc_b_data_fifo : entity work.async_fifo generic map(
        width => 16
    )port map(
        wclk => rx_core_clk(0),
        rclk => sys_clk_250M,
        rst => rx_rst_2,
        wdata_in => adc_b_data_buf_0,
        wen_in => adc_b_data_fifo_wen,
        rdata_out => adc_b_data_buf_1,
        ren_in => adc_b_data_fifo_ren,
        wrst_busy_out => adc_b_data_fifo_wrst_busy,
        rrst_busy_out => adc_b_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => adc_b_data_fifo_empty,
        wfull_out => adc_b_data_fifo_full,
        rfull_out => open
    );
    adc_b_data_fifo_wen <= not adc_b_data_fifo_full and not adc_b_data_fifo_wrst_busy and adc_dvalid;
    adc_b_data_fifo_ren <= not adc_b_data_fifo_empty and not adc_b_data_fifo_rrst_busy;
    process(sys_clk_250M)
    begin
        if rising_edge(sys_clk_250M) then
            adc_a_data_fifo_ren_1 <= adc_a_data_fifo_ren;
            adc_b_data_fifo_ren_1 <= adc_b_data_fifo_ren;
            if adc_a_data_fifo_ren_1 = '1' then
                adc_a_data <= adc_a_data_buf_1;
            end if;
            if adc_b_data_fifo_ren_1 = '1' then
                adc_b_data <= adc_b_data_buf_1;
            end if;
        end if;
    end process;

    dac_a_data_fifo : entity work.async_fifo generic map(
        width => 16
    )port map(
        wclk => sys_clk_250M,
        rclk => tx_core_clk(0),
        rst => sys_rst,
        wdata_in => dac_a_data,
        wen_in => dac_a_data_fifo_wen,
        rdata_out => dac_a_data_buf_1,
        ren_in => dac_a_data_fifo_ren,
        wrst_busy_out => dac_a_data_fifo_wrst_busy,
        rrst_busy_out => dac_a_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => dac_a_data_fifo_empty,
        wfull_out => dac_a_data_fifo_full,
        rfull_out => open
    );
    dac_a_data_fifo_wen <= not dac_a_data_fifo_full and not dac_a_data_fifo_wrst_busy;
    dac_a_data_fifo_ren <= not dac_a_data_fifo_empty and not dac_a_data_fifo_rrst_busy;
    dac_b_data_fifo : entity work.async_fifo generic map(
        width => 16
    )port map(
        wclk => sys_clk_250M,
        rclk => tx_core_clk(0),
        rst => sys_rst,
        wdata_in => dac_b_data,
        wen_in => dac_b_data_fifo_wen,
        rdata_out => dac_b_data_buf_1,
        ren_in => dac_b_data_fifo_ren,
        wrst_busy_out => dac_b_data_fifo_wrst_busy,
        rrst_busy_out => dac_b_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => dac_b_data_fifo_empty,
        wfull_out => dac_b_data_fifo_full,
        rfull_out => open
    );
    dac_b_data_fifo_wen <= not dac_b_data_fifo_full and not dac_b_data_fifo_wrst_busy;
    dac_b_data_fifo_ren <= not dac_b_data_fifo_empty and not dac_b_data_fifo_rrst_busy;
    process(tx_core_clk(0))
    begin
        if rising_edge(tx_core_clk(0)) then
            dac_a_data_fifo_ren_1 <= dac_a_data_fifo_ren;
            dac_b_data_fifo_ren_1 <= dac_b_data_fifo_ren;
            if dac_a_data_fifo_ren_1 = '1' then
                dac_a_data_buf_0 <= dac_a_data_buf_1;
            end if;
            if dac_b_data_fifo_ren_1 = '1' then
                dac_b_data_buf_0 <= dac_b_data_buf_1;
            end if;
        end if;
    end process;
    
    adc_spi_ss_fmc <= spi_ss(0);
    dac_spi_ss_fmc <= spi_ss(1);
    clk_spi_ss_fmc <= spi_ss(2);
    spi_sck_fmc <= spi_sck;
    spi_mosi_fmc <= spi_mosi;
    spi_miso <= adc_spi_miso_fmc when spi_ss(0) = '0' else
                   dac_spi_miso_fmc when spi_ss(1) = '0' else
                   clk_spi_miso_fmc when spi_ss(2) = '0' else
                   '0';
    spi_io_tri_fmc <= spi_io_tri;
    adc_pwdn_fmc <= '0';
    dac_rstn_fmc <= '1';
    dac_txen_fmc <= '1';
    eeprom_iic_scl_fmc <= '1';
    eeprom_iic_sda_fmc <= '0';
    ref_clk_p <= rx_core_clk_p_fmc;
    ref_clk_n <= rx_core_clk_n_fmc;
end architecture structural;