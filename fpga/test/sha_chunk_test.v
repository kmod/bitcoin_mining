`timescale 1ns / 1ps

////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer:
//
// Create Date:   01:32:00 07/21/2013
// Design Name:   sha256_chunk
// Module Name:   C:/Dropbox/xilinx/processor/test/sha_chunk_test.v
// Project Name:  processor
// Target Device:  
// Tool versions:  
// Description: 
//
// Verilog Test Fixture created by ISE for module: sha256_chunk
//
// Dependencies:
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
////////////////////////////////////////////////////////////////////////////////

module sha_chunk_test;

	// Inputs
	reg [511:0] data;
	reg [255:0] V_in;
	reg clk = 0;

	// Outputs
	wire [255:0] hash;

	// Instantiate the Unit Under Test (UUT)
	sha256_chunk uut (
		.clk(clk),
		.data(data), 
		.V_in(V_in), 
		.hash(hash)
	);
	
	parameter P=10;
	always #(P/2) clk = ~clk;

	initial begin
		// Initialize Inputs
		data = 0;
		data[7:0] = 8'd97;
		data[15:8] = 8'd98;
		data[23:16] = 8'd99;
		data[31:24] = 8'h80;
		data[511:504] = 8'd24;
		V_in = 256'h5be0cd191f83d9ab9b05688c510e527fa54ff53a3c6ef372bb67ae856a09e667;
		uut.roundnum = 6'h3e;
		
		#(80*P);
		
		$stop();

	end
      
endmodule

