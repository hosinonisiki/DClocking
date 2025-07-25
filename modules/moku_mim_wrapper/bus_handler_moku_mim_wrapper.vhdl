-- ///////////////Documentation////////////////////
-- This design handles all communication between
-- modules and the main control unit.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

use work.bus_protocol.all;

use work.moku_mim_config.all;

entity bus_handler_moku_mim_wrapper is
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        bus_en_in       :   in  std_logic;
        dbus_in         :   in  std_logic_vector(dbus_w - 1 downto 0);
        abus_in         :   in  std_logic_vector(abus_w - 1 downto 0);
        cbus_in         :   in  std_logic_vector(cbus_w - 1 downto 0);
        rsp_data_out    :   out std_logic_vector(rdbus_w - 1 downto 0);
        rsp_stat_out    :   out std_logic_vector(rsbus_w - 1 downto 0);
        wdata_out       :   out std_logic_vector(dbus_w - 1 downto 0);
        waddr_out       :   out std_logic_vector(abus_w - 1 downto 0);
        wmask_out       :   out std_logic_vector(dbus_w - 1 downto 0);
        wval_out        :   out std_logic;
        wen_out         :   out std_logic;
        rdata_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        raddr_out       :   out std_logic_vector(abus_w - 1 downto 0);
        rval_in         :   in  std_logic;
        ren_out         :   out std_logic;
        ram_rst_out     :   out std_logic;
        core_rst_out    :   out std_logic;
        -- Extra signals
        mim_en_out      :   out std_logic;
        mim_id_out      :   out std_logic_vector(5 downto 0) -- Allows a maximum of id up to 63
    );
end entity bus_handler_moku_mim_wrapper;

architecture behaviorial of bus_handler_moku_mim_wrapper is
    type state_type is (s_idle, s_handle_command, s_handle_write, s_handle_read, s_wait_response, s_handle_misc, s_misc_valid, s_error);
    signal state            :   state_type := s_idle;

    signal cmd_head_buf     :   std_logic_vector(cbus_w - 1 downto cbus_w - 2);
    signal cmd_body_buf     :   std_logic_vector(cbus_w - 3 downto 0);
    signal addr_buf         :   std_logic_vector(abus_w - 1 downto 0);
    signal data_buf         :   std_logic_vector(dbus_w - 1 downto 0);

    signal wval_reg         :   std_logic := '0';
    signal wen              :   std_logic;

    signal id_valid         :   std_logic;
begin
    -- FSM
    process(clk, rst)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= s_idle;
            else
                case state is
                    when s_idle =>
                        if bus_en_in = '1' and (or cbus_in) = '1' then
                            case cbus_in(cbus_w - 1 downto cbus_w - 2) is
                                when CONTROL_HEAD =>
                                    state <= s_handle_command;
                                when WRITE_HEAD =>
                                    state <= s_handle_write;
                                when READ_HEAD =>
                                    state <= s_handle_read;
                                when MISC_HEAD =>
                                    state <= s_handle_misc;
                                when others =>
                            end case;
                        end if;
                    when s_handle_command =>
                        -- All commands that currently exist only take one cycle to complete
                        state <= s_idle;
                    when s_handle_write =>
                        -- All writes that currently exist only take one cycle to complete
                        state <= s_idle;
                    when s_handle_read =>
                        -- Immediately pass the reading request and wait for the response
                        state <= s_wait_response;
                    when s_wait_response =>
                        if rval_in = '1' then
                            state <= s_idle;
                        end if;
                    when s_handle_misc =>
                        -- Check if the id is valid
                        if VALID_ID(to_integer(unsigned(data_buf(5 downto 0)))) = '1' then
                            state <= s_misc_valid;
                        else
                            state <= s_error;
                        end if;
                    when s_misc_valid =>
                        state <= s_idle;
                    when s_error =>
                        state <= s_idle;
                end case;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_idle then
                cmd_head_buf <= cbus_in(cbus_w - 1 downto cbus_w - 2);
                cmd_body_buf <= cbus_in(cbus_w - 3 downto 0);
                addr_buf <= abus_in;
                data_buf <= dbus_in;
            end if;
        end if;
    end process;

    -- handle commands
    process(clk)
    begin
        if rising_edge(clk) and state = s_handle_command then
            if cmd_body_buf = SET_CORE then
                core_rst_out <= '0';
            end if;
            if cmd_body_buf = RST_CORE then
                core_rst_out <= '1';
            end if;
            if cmd_body_buf = SET_RAM then
                ram_rst_out <= '0';
            end if;
            if cmd_body_buf = RST_RAM then
                ram_rst_out <= '1';
            end if;
        end if;
    end process;

    -- handle writes
    process(clk)
    begin
        if rising_edge(clk) then
            case state is
                when s_idle =>
                    wen <= '0';
                when s_handle_write =>
                    wdata_out <= data_buf;
                    waddr_out <= addr_buf;
                    if cmd_body_buf = WRITE_MASK or cmd_body_buf = WRITE_MASK_HOLD then
                        wmask_out <= dbus_in;
                    else
                        wmask_out <= (others => '1');
                    end if;
                    if cmd_body_buf = WRITE_HOLD or cmd_body_buf = WRITE_MASK_HOLD then
                        wval_reg <= '0';
                    else
                        wval_reg <= '1';
                    end if;
                    wen <= '1';
                when others =>
            end case;
        end if;
    end process;
    wen_out <= wen;
    wval_out <= wval_reg and not wen; -- Ensure that wval and wen won't be high at the same time
                                          -- This ensures a correct data flow
    
    -- handle reads
    process(clk)
    begin
        if rising_edge(clk) then
            case state is
                when s_idle =>
                    -- init
                    ren_out <= '0';
                when s_handle_read =>
                    raddr_out <= addr_buf;
                    ren_out <= '1';
                when s_wait_response =>
                    ren_out <= '0';
                when others =>
            end case;
        end if;
    end process;

    -- handle misc commands
    process(clk)
        variable id : integer;
    begin
        if rising_edge(clk) then
            if rst = '1' then
                mim_en_out <= '0';
            elsif state = s_misc_valid then
                -- Masks according to moku_mim_config
                mim_en_out <= data_buf(28);
                mim_id_out <= data_buf(5 downto 0);
            end if;
        end if;
    end process;

    -- handle replies
    process(clk)
    begin
        if rising_edge(clk) then
            case state is
                when s_idle =>
                    rsp_stat_out <= (others => '0');
                when s_handle_command =>
                    -- All commands that currently exist only take one cycle to complete
                    rsp_stat_out <= ROGER;
                when s_handle_write =>
                    -- All writes that currently exist only take one cycle to complete
                    rsp_stat_out <= ROGER;
                when s_wait_response =>
                    rsp_data_out <= rdata_in;
                    if rval_in = '1' then
                        rsp_stat_out <= ROGER;
                    end if;
                when s_misc_valid =>
                    -- All misc commands that currently exist only take one cycle to complete
                    rsp_stat_out <= ROGER;
                when s_error =>
                    rsp_stat_out <= ERROR;
                    rsp_data_out <= x"49564944"; -- "IVID" for invalid id
                when others =>
            end case;
        end if;
    end process;
end architecture behaviorial;
