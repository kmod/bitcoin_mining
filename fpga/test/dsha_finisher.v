`timescale 1ns / 1ps

////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer:
//
// Create Date:   03:54:36 07/21/2013
// Design Name:   dsha_finisher
// Module Name:   C:/Dropbox/bc/fpga/test/dsha_finisher.v
// Project Name:  processor
// Target Device:  
// Tool versions:  
// Description: 
//
// Verilog Test Fixture created by ISE for module: dsha_finisher
//
// Dependencies:
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
////////////////////////////////////////////////////////////////////////////////

module dsha_finisher_test;

	// Inputs
	reg clk;
	reg [255:0] X;
	reg [95:0] Y;
	reg [31:0] in_nonce;

	// Outputs
	wire [255:0] hash;
	wire [31:0] out_nonce;

	// Instantiate the Unit Under Test (UUT)
	dsha_finisher uut (
		.clk(clk), 
		.X(X), 
		.Y(Y), 
		.in_nonce(in_nonce), 
		.hash(hash), 
		.out_nonce(out_nonce)
	);
	
	parameter P=10;
	always #(P/2) clk = ~clk;


	initial begin
		// Initialize Inputs
		clk = 0;
		X = 256'h356d66244c73b9f1e1a328b2c6615412a965a72218c5c19eb5c5d4073db86a04;
		Y = 96'h1c2ac4af504e86edec9d69b1;
		in_nonce = 32'hb2957c02;
		uut.chunk1.roundnum = 6'h3e;
		uut.chunk2.roundnum = 6'h3e;

		#(135*P);
		$finish();
	end
      
endmodule

