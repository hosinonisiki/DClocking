-- Generated from Vivado custom IP axi interface template.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity uart_axi_master is
	generic (
		-- Users to add parameters here

		clk_freq				: integer 	:= clk_freq; -- Clock frequency in Hz
		baudrate				: integer 	:= baudrate; -- Baud rate for UART communication
		-- Despite the warning, parameters associated with the example are removed from the following section

		-- User parameters ends
		-- Do not modify the parameters beyond this line


		-- Parameters of Axi Master Bus Interface M00_AXI
		C_M00_AXI_ADDR_WIDTH	: integer	:= 32;
		C_M00_AXI_DATA_WIDTH	: integer	:= 32
	);
	port (
		-- Users to add ports here
		
		rst 		:	in 	std_logic;   -- System reset
		rst_busy	:	out std_logic;  -- Reset busy
		rxd_out		: 	out std_logic_vector(7 downto 0); -- UART receive data output
		rxen_in		: 	in 	std_logic;   -- UART receive enable input
		rxemp_out	: 	out std_logic;  -- UART receive empty output
		txd_in		: 	in 	std_logic_vector(7 downto 0); -- UART transmit data input
		txen_in		: 	in 	std_logic;   -- UART transmit enable input
		txful_out	: 	out std_logic;  -- UART transmit full output
		irpt		:	in  std_logic;   -- Interrupt request input from AXI UART 15500
		err			:	out std_logic;   -- Error indicator
		-- Despite the warning, ports associated with the example are removed from the following section

		-- User ports ends
		-- Do not modify the ports beyond this line


		-- Ports of Axi Master Bus Interface M00_AXI
		m00_axi_aclk	: in std_logic;
		m00_axi_aresetn	: in std_logic;
		m00_axi_awaddr	: out std_logic_vector(C_M00_AXI_ADDR_WIDTH-1 downto 0);
		m00_axi_awprot	: out std_logic_vector(2 downto 0);
		m00_axi_awvalid	: out std_logic;
		m00_axi_awready	: in std_logic;
		m00_axi_wdata	: out std_logic_vector(C_M00_AXI_DATA_WIDTH-1 downto 0);
		m00_axi_wstrb	: out std_logic_vector(C_M00_AXI_DATA_WIDTH/8-1 downto 0);
		m00_axi_wvalid	: out std_logic;
		m00_axi_wready	: in std_logic;
		m00_axi_bresp	: in std_logic_vector(1 downto 0);
		m00_axi_bvalid	: in std_logic;
		m00_axi_bready	: out std_logic;
		m00_axi_araddr	: out std_logic_vector(C_M00_AXI_ADDR_WIDTH-1 downto 0);
		m00_axi_arprot	: out std_logic_vector(2 downto 0);
		m00_axi_arvalid	: out std_logic;
		m00_axi_arready	: in std_logic;
		m00_axi_rdata	: in std_logic_vector(C_M00_AXI_DATA_WIDTH-1 downto 0);
		m00_axi_rresp	: in std_logic_vector(1 downto 0);
		m00_axi_rvalid	: in std_logic;
		m00_axi_rready	: out std_logic
	);
end uart_axi_master;

architecture arch_imp of uart_axi_master is

	-- component declaration
	component uart_axi_master_M00_AXI is
		generic (
		clk_freq			: integer 	:= 250_000_000;
		baudrate			: integer 	:= 19200;

		C_M_AXI_ADDR_WIDTH	: integer	:= 32;
		C_M_AXI_DATA_WIDTH	: integer	:= 32
		);
		port (
		rst			:	in 	std_logic;
		rst_busy	:	out std_logic;
		rxd_out		: 	out std_logic_vector(7 downto 0);
		rxen_in		: 	in 	std_logic;
		rxemp_out	: 	out std_logic;
		txd_in		: 	in 	std_logic_vector(7 downto 0);
		txen_in		: 	in 	std_logic;
		txful_out	: 	out std_logic;
		irpt		:	in  std_logic;
		err			:	out std_logic;

		M_AXI_ACLK	: in std_logic;
		M_AXI_ARESETN	: in std_logic;
		M_AXI_AWADDR	: out std_logic_vector(C_M_AXI_ADDR_WIDTH-1 downto 0);
		M_AXI_AWPROT	: out std_logic_vector(2 downto 0);
		M_AXI_AWVALID	: out std_logic;
		M_AXI_AWREADY	: in std_logic;
		M_AXI_WDATA	: out std_logic_vector(C_M_AXI_DATA_WIDTH-1 downto 0);
		M_AXI_WSTRB	: out std_logic_vector(C_M_AXI_DATA_WIDTH/8-1 downto 0);
		M_AXI_WVALID	: out std_logic;
		M_AXI_WREADY	: in std_logic;
		M_AXI_BRESP	: in std_logic_vector(1 downto 0);
		M_AXI_BVALID	: in std_logic;
		M_AXI_BREADY	: out std_logic;
		M_AXI_ARADDR	: out std_logic_vector(C_M_AXI_ADDR_WIDTH-1 downto 0);
		M_AXI_ARPROT	: out std_logic_vector(2 downto 0);
		M_AXI_ARVALID	: out std_logic;
		M_AXI_ARREADY	: in std_logic;
		M_AXI_RDATA	: in std_logic_vector(C_M_AXI_DATA_WIDTH-1 downto 0);
		M_AXI_RRESP	: in std_logic_vector(1 downto 0);
		M_AXI_RVALID	: in std_logic;
		M_AXI_RREADY	: out std_logic
		);
	end component uart_axi_master_M00_AXI;

begin

-- Instantiation of Axi Bus Interface M00_AXI
uart_axi_master_M00_AXI_inst : uart_axi_master_M00_AXI
	generic map (
		clk_freq			=> clk_freq,
		baudrate			=> baudrate,

		C_M_AXI_ADDR_WIDTH	=> C_M00_AXI_ADDR_WIDTH,
		C_M_AXI_DATA_WIDTH	=> C_M00_AXI_DATA_WIDTH
	)
	port map (
		rst		=> rst,
		rst_busy	=> rst_busy,
		rxd_out		=> rxd_out,
		rxen_in		=> rxen_in,
		rxemp_out	=> rxemp_out,
		txd_in		=> txd_in,
		txen_in		=> txen_in,
		txful_out	=> txful_out,
		irpt		=> irpt,
		err			=> err,
		
		M_AXI_ACLK	=> m00_axi_aclk,
		M_AXI_ARESETN	=> m00_axi_aresetn,
		M_AXI_AWADDR	=> m00_axi_awaddr,
		M_AXI_AWPROT	=> m00_axi_awprot,
		M_AXI_AWVALID	=> m00_axi_awvalid,
		M_AXI_AWREADY	=> m00_axi_awready,
		M_AXI_WDATA	=> m00_axi_wdata,
		M_AXI_WSTRB	=> m00_axi_wstrb,
		M_AXI_WVALID	=> m00_axi_wvalid,
		M_AXI_WREADY	=> m00_axi_wready,
		M_AXI_BRESP	=> m00_axi_bresp,
		M_AXI_BVALID	=> m00_axi_bvalid,
		M_AXI_BREADY	=> m00_axi_bready,
		M_AXI_ARADDR	=> m00_axi_araddr,
		M_AXI_ARPROT	=> m00_axi_arprot,
		M_AXI_ARVALID	=> m00_axi_arvalid,
		M_AXI_ARREADY	=> m00_axi_arready,
		M_AXI_RDATA	=> m00_axi_rdata,
		M_AXI_RRESP	=> m00_axi_rresp,
		M_AXI_RVALID	=> m00_axi_rvalid,
		M_AXI_RREADY	=> m00_axi_rready
	);

	-- Add user logic here

	-- User logic ends

end arch_imp;





library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity uart_axi_master_M00_AXI is
	generic (
		-- Users to add parameters here

		clk_freq			: integer 	:= 250_000_000; -- Clock frequency in Hz
		baudrate			: integer 	:= 19200; -- Baud rate for UART communication
		-- Despite the warning, parameters associated with the example are removed from the following section

		-- User parameters ends
		-- Do not modify the parameters beyond this line

		-- Width of M_AXI address bus. 
    -- The master generates the read and write addresses of width specified as C_M_AXI_ADDR_WIDTH.
		C_M_AXI_ADDR_WIDTH	: integer	:= 32;
		-- Width of M_AXI data bus. 
    -- The master issues write data and accept read data where the width of the data bus is C_M_AXI_DATA_WIDTH
		C_M_AXI_DATA_WIDTH	: integer	:= 32
	);
	port (
		-- Users to add ports here

		-- System reset input, active high.
		-- To be distinguished from ARESETN.
		rst			:	in 	std_logic;
		-- Reset busy output, asserts when the reset is in progress.
		-- Initialization of AXI UART 15500 is done in this process.
		rst_busy	:	out std_logic;
		-- UART receive data output.
		rxd_out		: 	out std_logic_vector(7 downto 0);
		-- UART receive enable input, data is considered sent on the next rising edge of M_AXI_ACLK
		-- once rxen_in asserts while rxemp_out is being deasserted.
		rxen_in		: 	in 	std_logic;
		-- UART receive empty output, asserts when there is no data to be received.
		-- Data should be ready at rxd_out when rxemp_out deasserts.
		rxemp_out	: 	out std_logic;
		-- UART transmit data input.
		txd_in		: 	in 	std_logic_vector(7 downto 0);
		-- UART transmit enable input, data is considered sent on the next rising edge of M_AXI_ACLK
		-- once txen_in asserts while txful_out is being deasserted.
		txen_in		: 	in 	std_logic;
		-- UART transmit full output, asserts when a transmission
		-- from this master to AXI UART 15500's txFIFO is in progress.
		txful_out	: 	out std_logic;
		-- Interrupt request input from AXI UART 15500.
		irpt		:	in  std_logic;
		-- Error indicator
		err 		:	out std_logic;
		-- Despite the warning, ports associated with the example are removed from the following section

		-- User ports ends
		-- Do not modify the ports beyond this line

		-- AXI clock signal
		M_AXI_ACLK	: in std_logic;
		-- AXI active low reset signal
		M_AXI_ARESETN	: in std_logic;
		-- Master Interface Write Address Channel ports. Write address (issued by master)
		M_AXI_AWADDR	: out std_logic_vector(C_M_AXI_ADDR_WIDTH-1 downto 0);
		-- Write channel Protection type.
    -- This signal indicates the privilege and security level of the transaction,
    -- and whether the transaction is a data access or an instruction access.
		M_AXI_AWPROT	: out std_logic_vector(2 downto 0);
		-- Write address valid. 
    -- This signal indicates that the master signaling valid write address and control information.
		M_AXI_AWVALID	: out std_logic;
		-- Write address ready. 
    -- This signal indicates that the slave is ready to accept an address and associated control signals.
		M_AXI_AWREADY	: in std_logic;
		-- Master Interface Write Data Channel ports. Write data (issued by master)
		M_AXI_WDATA	: out std_logic_vector(C_M_AXI_DATA_WIDTH-1 downto 0);
		-- Write strobes. 
    -- This signal indicates which byte lanes hold valid data.
    -- There is one write strobe bit for each eight bits of the write data bus.
		M_AXI_WSTRB	: out std_logic_vector(C_M_AXI_DATA_WIDTH/8-1 downto 0);
		-- Write valid. This signal indicates that valid write data and strobes are available.
		M_AXI_WVALID	: out std_logic;
		-- Write ready. This signal indicates that the slave can accept the write data.
		M_AXI_WREADY	: in std_logic;
		-- Master Interface Write Response Channel ports. 
    -- This signal indicates the status of the write transaction.
		M_AXI_BRESP	: in std_logic_vector(1 downto 0);
		-- Write response valid. 
    -- This signal indicates that the channel is signaling a valid write response
		M_AXI_BVALID	: in std_logic;
		-- Response ready. This signal indicates that the master can accept a write response.
		M_AXI_BREADY	: out std_logic;
		-- Master Interface Read Address Channel ports. Read address (issued by master)
		M_AXI_ARADDR	: out std_logic_vector(C_M_AXI_ADDR_WIDTH-1 downto 0);
		-- Protection type. 
    -- This signal indicates the privilege and security level of the transaction, 
    -- and whether the transaction is a data access or an instruction access.
		M_AXI_ARPROT	: out std_logic_vector(2 downto 0);
		-- Read address valid. 
    -- This signal indicates that the channel is signaling valid read address and control information.
		M_AXI_ARVALID	: out std_logic;
		-- Read address ready. 
    -- This signal indicates that the slave is ready to accept an address and associated control signals.
		M_AXI_ARREADY	: in std_logic;
		-- Master Interface Read Data Channel ports. Read data (issued by slave)
		M_AXI_RDATA	: in std_logic_vector(C_M_AXI_DATA_WIDTH-1 downto 0);
		-- Read response. This signal indicates the status of the read transfer.
		M_AXI_RRESP	: in std_logic_vector(1 downto 0);
		-- Read valid. This signal indicates that the channel is signaling the required read data.
		M_AXI_RVALID	: in std_logic;
		-- Read ready. This signal indicates that the master can accept the read data and response information.
		M_AXI_RREADY	: out std_logic
	);
end uart_axi_master_M00_AXI;

-- Removed the example along with associated declarations.
architecture implementation of uart_axi_master_M00_AXI is
	type state_type is (s_init, s_idle, s_irpt, s_err, s_rx, s_tx);
	signal state	: state_type := s_init;

	signal init_begin	: std_logic := '0'; -- Initialization begin signal
	signal init_done	: std_logic := '0'; -- Initialization done signal
	signal txful 		: std_logic := '0'; -- Transmit full signal
	signal rxemp 		: std_logic := '1'; -- Receive empty signal
	signal tx_buf 		: std_logic_vector(7 downto 0) := (others => '0'); -- Internal transmitter buffer
	signal rx_buf		: std_logic_vector(7 downto 0) := (others => '0'); -- Internal receiver buffer

	constant divisor	: integer := clk_freq / (baudrate * 16); -- 16x oversampling
	constant divisor_uint	: unsigned(15 downto 0) := to_unsigned(divisor, 16);
	constant divisor_lsb	: std_logic_vector(7 downto 0) := std_logic_vector(divisor_uint(7 downto 0));
	constant divisor_msb	: std_logic_vector(7 downto 0) := std_logic_vector(divisor_uint(15 downto 8));

	type lut_address_type is array(natural range <>) of std_logic_vector(C_M_AXI_ADDR_WIDTH - 1 downto 0);
	type lut_data_type is array(natural range <>) of std_logic_vector(C_M_AXI_DATA_WIDTH - 1 downto 0);
	-- Initialization sequence:
	-- Set LCR(7) to 1 (0x100C 0x0080)
	-- Set divisor latches (0x1000 lsb, 0x1004 msb)
	-- Set FCR (0x1008, 0x0001)
	-- Set LCR 
	-- Set LCR(7) to 0 (0x100C 0x001B)
	-- Set IER (0x1004, 0x0005)
	constant lut_init_size	: integer := 8; -- Number of initialization steps, must be power of 2
	constant lut_address_init	: lut_address_type(0 to lut_init_size - 1) := (
		x"0000_100C",
		x"0000_1000",
		x"0000_1004",
		x"0000_1008",
		x"0000_100C",
		x"0000_1004",
		x"0000_101C", -- Scratch register, pad lut size to power of 2 and avoid undefined behavior
		x"0000_101C"
	);
	constant lut_data_init		: lut_data_type(0 to lut_init_size - 1) := (
		x"0000_0080",
		x"0000_00" & divisor_lsb,
		x"0000_00" & divisor_msb,
		x"0000_0001",
		x"0000_001B",
		x"0000_0005",
		x"0000_0000", -- Scratch register, pad lut size to power of 2 and avoid undefined behavior
		x"0000_0000"
	);
	signal lut_index	: unsigned(2 downto 0) := (others => '0'); -- Index for the initialization LUT

	-- AXI4LITE signals
	--write address valid
	signal axi_awvalid	: std_logic;
	--write data valid
	signal axi_wvalid	: std_logic;
	--read address valid
	signal axi_arvalid	: std_logic;
	--read data acceptance
	signal axi_rready	: std_logic;
	--write response acceptance
	signal axi_bready	: std_logic;
	--write address
	signal axi_awaddr	: std_logic_vector(C_M_AXI_ADDR_WIDTH-1 downto 0);
	--write data
	signal axi_wdata	: std_logic_vector(C_M_AXI_DATA_WIDTH-1 downto 0);
	--read addresss
	signal axi_araddr	: std_logic_vector(C_M_AXI_ADDR_WIDTH-1 downto 0);
	--Asserts when there is a write response error
	signal write_resp_error	: std_logic;
	--Asserts when there is a read response error
	signal read_resp_error	: std_logic;
	--A pulse to initiate a write transaction
	signal start_single_write	: std_logic := '0';
	--A pulse to initiate a read transaction
	signal start_single_read	: std_logic := '0';

begin
	-- I/O Connections assignments

	--Adding the offset address to the base addr of the slave
	M_AXI_AWADDR	<= axi_awaddr;
	--AXI 4 write data
	M_AXI_WDATA	<= axi_wdata;
	M_AXI_AWPROT	<= "000";
	M_AXI_AWVALID	<= axi_awvalid;
	--Write Data(W)
	M_AXI_WVALID	<= axi_wvalid;
	--Set all byte strobes in this example
	M_AXI_WSTRB	<= "1111";
	--Write Response (B)
	M_AXI_BREADY	<= axi_bready;
	--Read Address (AR)
	M_AXI_ARADDR	<= axi_araddr;
	M_AXI_ARVALID	<= axi_arvalid;
	M_AXI_ARPROT	<= "001";
	--Read and Read Response (R)
	M_AXI_RREADY	<= axi_rready;


	----------------------
	--Write Address Channel
	----------------------

	-- The purpose of the write address channel is to request the address and 
	-- command information for the entire transaction.  It is a single beat
	-- of information.

	-- Note for this example the axi_awvalid/axi_wvalid are asserted at the same
	-- time, and then each is deasserted independent from each other.
	-- This is a lower-performance, but simplier control scheme.

	-- AXI VALID signals must be held active until accepted by the partner.

	-- A data transfer is accepted by the slave when a master has
	-- VALID data and the slave acknoledges it is also READY. While the master
	-- is allowed to generated multiple, back-to-back requests by not 
	-- deasserting VALID, this design will add rest cycle for
	-- simplicity.

	-- Since only one outstanding transaction is issued by the user design,
	-- there will not be a collision between a new request and an accepted
	-- request on the same clock cycle. 

	process(M_AXI_ACLK)                                                          
	begin                                                                             
	    if (rising_edge (M_AXI_ACLK)) then                                              
			--Only VALID signals must be deasserted during reset per AXI spec             
			--Consider inverting then registering active-low reset for higher fmax        
			if (M_AXI_ARESETN = '0') then                                                
				axi_awvalid <= '0';                                                         
			else                                                                                                                            
				--Signal a new address/data command is available by user logic              
				if (start_single_write = '1') then                                          
					axi_awvalid <= '1';                                                       
				elsif (M_AXI_AWREADY = '1' and axi_awvalid = '1') then                      
					--Address accepted by interconnect/slave (issue of M_AXI_AWREADY by slave)
					axi_awvalid <= '0';                                                       
				end if;                                                                                       
			end if;                                                                       
	    end if;                                                                         
	end process;                                                                                                                                      


	----------------------
	--Write Data Channel
	----------------------

	--The write data channel is for transfering the actual data.
	--The data generation is speific to the example design, and 
	--so only the WVALID/WREADY handshake is shown here

	   process(M_AXI_ACLK)                                                 
	   begin                                                                         
	     if (rising_edge (M_AXI_ACLK)) then                                          
	       if (M_AXI_ARESETN = '0' ) then                                            
	         axi_wvalid <= '0';                                                      
	       else                                                                      
	         if (start_single_write = '1') then                                      
	           --Signal a new address/data command is available by user logic        
	           axi_wvalid <= '1';                                                    
	         elsif (M_AXI_WREADY = '1' and axi_wvalid = '1') then                    
	           --Data accepted by interconnect/slave (issue of M_AXI_WREADY by slave)
	           axi_wvalid <= '0';                                                    
	         end if;                                                                 
	       end if;                                                                   
	     end if;                                                                     
	   end process;                                                                  


	------------------------------
	--Write Response (B) Channel
	------------------------------

	--The write response channel provides feedback that the write has committed
	--to memory. BREADY will occur after both the data and the write address
	--has arrived and been accepted by the slave, and can guarantee that no
	--other accesses launched afterwards will be able to be reordered before it.

	--The BRESP bit [1] is used indicate any errors from the interconnect or
	--slave for the entire write burst. This example will capture the error.

	--While not necessary per spec, it is advisable to reset READY signals in
	--case of differing reset latencies between master/slave.

	  process(M_AXI_ACLK)                                            
	  begin                                                                
	    if (rising_edge (M_AXI_ACLK)) then                                 
	      if (M_AXI_ARESETN = '0') then                                   
	        axi_bready <= '0';                                             
	      else                                                             
	        if (M_AXI_BVALID = '1' and axi_bready = '0') then              
	          -- accept/acknowledge bresp with axi_bready by the master    
	          -- when M_AXI_BVALID is asserted by slave                    
	           axi_bready <= '1';                                          
	        elsif (axi_bready = '1') then                                  
	          -- deassert after one clock cycle                            
	          axi_bready <= '0';                                           
	        end if;                                                        
	      end if;                                                          
	    end if;                                                            
	  end process;                                                         
	--Flag write errors                                                    
	  write_resp_error <= (axi_bready and M_AXI_BVALID and M_AXI_BRESP(1));


	------------------------------
	--Read Address Channel
	------------------------------                                                                 
	                                                                                   
	  -- A new axi_arvalid is asserted when there is a valid read address              
	  -- available by the master. start_single_read triggers a new read                
	  -- transaction                                                                   
	  process(M_AXI_ACLK)                                                              
	  begin                                                                            
	    if (rising_edge (M_AXI_ACLK)) then                                             
	      if (M_AXI_ARESETN = '0') then                                               
	        axi_arvalid <= '0';                                                        
	      else                                                                         
	        if (start_single_read = '1') then                                          
	          --Signal a new read address command is available by user logic           
	          axi_arvalid <= '1';                                                      
	        elsif (M_AXI_ARREADY = '1' and axi_arvalid = '1') then                     
	        --RAddress accepted by interconnect/slave (issue of M_AXI_ARREADY by slave)
	          axi_arvalid <= '0';                                                      
	        end if;                                                                    
	      end if;                                                                      
	    end if;                                                                        
	  end process;                                                                     


	----------------------------------
	--Read Data (and Response) Channel
	----------------------------------

	--The Read Data channel returns the results of the read request 
	--The master will accept the read data by asserting axi_rready
	--when there is a valid read data available.
	--While not necessary per spec, it is advisable to reset READY signals in
	--case of differing reset latencies between master/slave.

	  process(M_AXI_ACLK)                                             
	  begin                                                                 
	    if (rising_edge (M_AXI_ACLK)) then                                  
	      if (M_AXI_ARESETN = '0') then                                    
	        axi_rready <= '1';                                              
	      else                                                              
	        if (M_AXI_RVALID = '1' and axi_rready = '0') then               
	         -- accept/acknowledge rdata/rresp with axi_rready by the master
	         -- when M_AXI_RVALID is asserted by slave                      
	          axi_rready <= '1';                                            
	        elsif (axi_rready = '1') then                                   
	          -- deassert after one clock cycle                             
	          axi_rready <= '0';                                            
	        end if;                                                         
	      end if;                                                           
	    end if;                                                             
	  end process;                                                          
	                                                                        
	--Flag write errors                                                     
	  read_resp_error <= (axi_rready and M_AXI_RVALID and M_AXI_RRESP(1));  


	----------------------------------
	--User Logic
	----------------------------------

	-- Example removed completely.

	-- Temporary note:
	-- Signals to deal with : rst_busy, rxd_out, rxen_in, rxemp_out,
	-- txd_in, txen_in, txful_out, irpt
	-- AXI input signals : AWREADY, WREADY, BRESP, BVALID, ARREADY, RVALID, RRESP, RDATA
	-- AXI output signals : AWADDR, AWVALID, WDATA, WVALID, BREADY, ARADDR, ARVALID, RREADY

	-- Initialization sequence:
	-- Set LCR(7) to 1
	-- Set divisor latches
	-- Set FCR
	-- Set LCR
	-- Set LCR(7) to 0
	-- Set IER

	-- FSM
	process(M_AXI_ACLK)
	begin
		if rising_edge(M_AXI_ACLK) then
			if rst = '1' then
				-- Reset to initialization state
				state <= s_init;
			else
				case state is
					when s_init =>
						-- Initialize AXI UART 15500
						if init_done = '1' then
							state <= s_idle;
						end if;
					when s_idle =>
						if irpt = '1' then
							-- Handle interrupt
							state <= s_irpt;
						elsif txful = '1' then
							state <= s_tx;
						end if;
					when s_irpt =>
						-- Initiate a read transaction to get the interrupt status
						if M_AXI_RVALID = '1' and axi_rready = '1' then
							if M_AXI_RDATA(3 downto 1) = "010" and M_AXI_RRESP(1) = '0' then
								state <= s_rx; -- Received data
							else
								state <= s_err; -- Error in interrupt handling
							end if;
						end if;
					when s_err =>
						-- Wait for user command to reset
					when s_rx =>
						if M_AXI_RVALID = '1' and axi_rready = '1' then
							if read_resp_error = '0' then
								state <= s_idle; -- Received data, go back to idle
							else
								state <= s_err; -- Error in read response
							end if;
						end if;
					when s_tx =>
						if M_AXI_BVALID = '1' and axi_bready = '1' then
							if write_resp_error = '0' then
								state <= s_idle; -- Data sent, go back to idle
							else
								state <= s_err; -- Error in write response
							end if;
						end if;
				end case;
			end if;
		end if;
	end process;

	-- Write control
	process(M_AXI_ACLK)
	begin
		if rising_edge(M_AXI_ACLK) then
			if rst = '1' then
				start_single_write <= '0';
			elsif start_single_write = '1' then
				start_single_write <= '0'; -- Deassert after one clock cycle
			else
				case state is
					when s_init =>
						if init_begin = '1' then
							start_single_write <= '1'; -- Start initialization
						elsif M_AXI_BVALID = '1' and axi_bready = '1' and init_done = '0' then
							start_single_write <= '1'; -- Continue initialization, ignore potential errors
						end if;
					when s_idle =>
						if txful = '1' then
							start_single_write <= '1'; -- Start transmission
						end if;
					when others =>
						-- Do nothing
				end case;
			end if;
		end if;
	end process;

	process(M_AXI_ACLK)
	begin
		if rising_edge(M_AXI_ACLK) then
			if rst = '1' then
				axi_awaddr <= (others => '0');
				axi_wdata <= (others => '0');
			else
				if start_single_write = '1' then
					case state is
						when s_init =>
							axi_awaddr <= lut_address_init(to_integer(lut_index));
							axi_wdata <= lut_data_init(to_integer(lut_index));
						when s_tx =>
							axi_awaddr <= x"0000_1000"; -- AXI UART 15500 Transmitter Holding Register
							axi_wdata <= x"0000_00" & tx_buf; -- Transmit data
						when others =>
							-- Shouldn't occur
					end case;
				end if;
			end if;
		end if;
	end process;

	-- Read control
	process(M_AXI_ACLK)
	begin 
		if rising_edge(M_AXI_ACLK) then
			if rst = '1' then
				start_single_read <= '0';
			elsif start_single_read = '1' then
				start_single_read <= '0'; -- Deassert after one clock cycle
			else
				case state is
					when s_idle =>
						if irpt = '1' then
							start_single_read <= '1'; -- Start read transaction to get interrupt status
						end if;
					when s_irpt =>
						if M_AXI_RVALID = '1' AND axi_rready = '1' and M_AXI_RDATA(3 downto 1 ) = "010" and M_AXI_RRESP(1) = '0' then
							start_single_read <= '1'; -- Read received data
						end if;
					when others =>
						-- Do nothing
				end case;
			end if;
		end if;
	end process;

	process(M_AXI_ACLK)
	begin
		if rising_edge(M_AXI_ACLK) then
			if rst = '1' then
				axi_araddr <= (others => '0');
			else
				if start_single_read = '1' then
					case state is
						when s_irpt =>
							axi_araddr <= x"0000_1008";
						when s_rx =>
							axi_araddr <= x"0000_1000";
						when others =>
							-- Shouldn't occur
					end case;
				end if;
			end if;
		end if;
	end process;
				
	-- Initialization control
	process(M_AXI_ACLK)
	begin
		if rising_edge(M_AXI_ACLK) then
			if rst = '1' then
				lut_index <= (others => '0');
			else
				if state = s_init and start_single_write = '1' then
					lut_index <= lut_index + "001";
				end if;
			end if;
		end if;
	end process;

	process(M_AXI_ACLK)
	begin
		if rising_edge(M_AXI_ACLK) then
			if rst = '1' then
				init_begin <= '1';
			elsif init_begin = '1' then
				init_begin <= '0'; -- Deassert one clock cycle after reset deasserts
			end if;
		end if;
	end process;

	init_done <= '1' when state = s_init and M_AXI_BVALID = '1' and axi_bready = '1' and lut_index = "000" else '0';

	rst_busy <= '1' when state = s_init else '0';

	err <= '1' when state = s_err else '0'; -- Error indicator

	-- Interface to custom design
	-- Temporary note:
	-- Signals to deal with : rxd_out, rxen_in, rxemp_out, txd_in, txen_in, txful_out, rxemp, txful, tx_buf, rx_buf

	-- Rx

	process(M_AXI_ACLK)
	begin
		if rising_edge(M_AXI_ACLK) then
			if rst = '1' then
				rxd_out <= (others => '0');
			else
				rxd_out <= rx_buf; -- Keep rxd_out in track with the received data
			end if;
		end if;
	end process;

	process(M_AXI_ACLK)
	begin
		if rising_edge(M_AXI_ACLK) then
			if rst = '1' then
				rxemp <= '1';
			elsif state = s_rx and M_AXI_RVALID = '1' and axi_rready = '1' then
				rxemp <= '0';
			elsif rxemp = '0' and rxen_in = '1' then
				rxemp <= '1'; -- Deassert when rxen_in is asserted
			end if;
		end if;
	end process;

	rxemp_out <= rxemp;

	process(M_AXI_ACLK)
	begin
		if rising_edge(M_AXI_ACLK) then
			if rst = '1' then
				rx_buf <= (others => '0');
			elsif state = s_rx and M_AXI_RVALID = '1' and axi_rready = '1' then
				rx_buf <= M_AXI_RDATA(7 downto 0); -- Store received data in rx_buf
			end if;
		end if;
	end process;

	-- Tx

	process(M_AXI_ACLK)
	begin
		if rising_edge(M_AXI_ACLK) then
			if rst = '1' then
				txful <= '0';
			elsif state = s_tx and M_AXI_BVALID = '1' and axi_bready = '1' then
				txful <= '0'; -- Deassert txful when write response is received
			elsif txful = '0' and txen_in = '1' then
				txful <= '1'; -- Assert txful when txen_in is asserted
			end if;
		end if;
	end process;

	txful_out <= txful;

	process(M_AXI_ACLK)
	begin
		if rising_edge(M_AXI_ACLK) then
			if rst = '1' then
				tx_buf <= (others => '0');
			elsif txful = '0' and txen_in = '1' then
				tx_buf <= txd_in; -- Load tx_buf with data to be sent
			end if;
		end if;
	end process;

end implementation;
