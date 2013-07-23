`timescale 1ns / 1ps
`default_nettype none
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    04:12:55 07/16/2013 
// Design Name: 
// Module Name:    fpga 
// Project Name: 
// Target Devices: 
// Tool versions: 
// Description: 
//
// Dependencies: 
//
// Revision: 
// Revision 0.01 - File Created
// Additional Comments: 
//
//////////////////////////////////////////////////////////////////////////////////
module fpga(
		input wire input_clk,
		input wire [7:0] sw,
		input wire [4:0] btn,
		output wire [7:0] led,
		output wire [7:0] seg,
		output wire [3:0] an,
		output wire RsTx,
		input wire RsRx
	);

	wire clk; // 10MHz clock
	dcm dcm(.CLK_IN(input_clk), .CLK_OUT(clk)); // 100MHz -> 10MHz DCM

	assign led = sw;
	
	// button synchronizer:
	reg [4:0] btn_sync, btn_sync2;
	always @(posedge clk) begin
		{btn_sync, btn_sync2} <= {btn, btn_sync};
	end
	
	wire [4:0] btn_debounced;
	genvar idx;
	generate
		for (idx=0; idx<5; idx=idx+1) begin: debounce_btn
			debounce btn_db(.clk(clk), .in(btn_sync2[idx]), .out(btn_debounced[idx]));
		end
	endgenerate
	
	reg [4:0] btn_prev;
	
	wire [15:0] sseg_data;
	assign sseg_data = in_nonce[31:16];
	sseg #(.N(16)) sseg(.clk(clk), .in(sseg_data), .c(seg), .an(an));
	
	
	/*
	Baud rates
	Baud\MHz		10		50		80		100
	115200		87		434	694	868
	*/
	
	wire uart_tx_req, uart_tx_ready;
	wire [255:0] uart_tx_data;
	assign uart_tx_data[7:0] = 8'haa;
	assign uart_tx_data[39:8] = out_nonce;
	assign uart_tx_data[47:40] = 8'haa;
	assign uart_tx_data[255:192] = 64'hdead432987beefaa;
	assign uart_tx_req = success;
	uart_multibyte_transmitter #(.CLK_CYCLES(694), .MSG_LOG_WIDTH(5)) uart_mbtx(.clk(clk), .data(uart_tx_data), .req(uart_tx_req), .uart_tx(RsTx));
	
	// Input synchronizer:
	reg RsRx1=1, RsRx2=1;
	always @(posedge clk) begin
		{RsRx1, RsRx2} <= {RsRx, RsRx1};
	end
	wire uart_rx_valid;
	wire [511:0] uart_rx_data;
	wire [255:0] X;
	wire [95:0] Y;
	assign X = uart_rx_data[255:0]; // ex 256'h356d66244c73b9f1e1a328b2c6615412a965a72218c5c19eb5c5d4073db86a04
	assign Y = uart_rx_data[351:256]; // ex 96'h1c2ac4af504e86edec9d69b1
	//assign nonce = uart_rx_data[383:352]; // ex 32'hb2957c02
	
	reg [31:0] in_nonce = 32'h0;
	
	always @(posedge clk) begin
		if (accepted) in_nonce <= in_nonce + 1;
	end
	
	uart_multibyte_receiver #(.CLK_CYCLES(694), .MSG_LOG_WIDTH(6)) uart_mbrx(.clk(clk), .data(uart_rx_data), .valid(uart_rx_valid), .ack(1'b0), .uart_rx(RsRx2));
	
	
	reg [31:0] out_nonce;
	wire accepted, success;
	
	localparam NUM_COPIES = 4;
	wire [255:0] _out_hash[NUM_COPIES-1:0];
	wire [31:0] _out_nonce[NUM_COPIES-1:0];
	wire [NUM_COPIES-1:0] _dsha_accepted, _dsha_success;
	generate	
		for (idx = 0; idx < NUM_COPIES; idx = idx + 1) begin: block_dsha
			assign _dsha_success[idx] = (_out_hash[idx][255:224+8] == 0) && (sw[0] || (_out_hash[idx][231:224] == 0));
			dsha_finisher #(.START_ROUND(idx)) dsha(.clk(clk), .X(X), .Y(Y), .in_nonce(in_nonce), .hash(_out_hash[idx]), .out_nonce(_out_nonce[idx]), .accepted(_dsha_accepted[idx]));
		end
	endgenerate
	integer i;
	always @(*) begin
		out_nonce = _out_nonce[0];
		
		/*if (_dsha_success[1]) begin
			out_nonce = _out_nonce[1];
		end
		if (_dsha_success[2]) begin
			out_nonce = _out_nonce[2];
		end*/
		for (i = 1; i < NUM_COPIES; i = i + 1) begin
			if (_dsha_success[i]) begin
				out_nonce = _out_nonce[i];
			end
		end
	end
	assign accepted = (_dsha_accepted != 0);
	assign success = (_dsha_success != 0);
	
	/*wire [255:0] out_hash1;
	wire [31:0] out_nonce1;
	wire dsha_accepted1, success1;
	assign success1 = (out_hash1[255:224+8] == 0);
	dsha_finisher #(.START_ROUND(0)) dsha1(.clk(clk), .X(X), .Y(Y), .in_nonce(in_nonce), .hash(out_hash1), .out_nonce(out_nonce1), .accepted(dsha_accepted1));
	wire [255:0] out_hash2;
	wire [31:0] out_nonce2;
	wire dsha_accepted2, success2;
	assign success2 = (out_hash2[255:224+8] == 0);
	dsha_finisher #(.START_ROUND(8)) dsha2(.clk(clk), .X(X), .Y(Y), .in_nonce(in_nonce), .hash(out_hash2), .out_nonce(out_nonce2), .accepted(dsha_accepted2));
	wire [255:0] out_hash3;
	wire [31:0] out_nonce3;
	wire dsha_accepted3, success3;
	assign success3 = (out_hash3[255:224+8] == 0);
	dsha_finisher #(.START_ROUND(16)) dsha3(.clk(clk), .X(X), .Y(Y), .in_nonce(in_nonce), .hash(out_hash3), .out_nonce(out_nonce3), .accepted(dsha_accepted3));
	
	assign success = (success1 || success2 || success3);
	assign accepted = (dsha_accepted1 || dsha_accepted2 || dsha_accepted3);
	assign out_hash = (success1 ? out_hash1 : (success2 ? out_hash2 : out_hash3));
	assign out_nonce = (success1 ? out_nonce1 : (success2 ? out_nonce2 : out_nonce3));*/
	
	
	
	always @(posedge clk) begin
		btn_prev <= btn_debounced;
	end
endmodule
