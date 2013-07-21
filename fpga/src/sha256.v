`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    21:50:01 07/20/2013 
// Design Name: 
// Module Name:    sha256 
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

module karray(
		input wire [5:0] idx, output reg [31:0] k
	);
	always @(*) begin
		case (idx)
			6'b000000: k = 32'h428a2f98;
			6'b000001: k = 32'h71374491;
			6'b000010: k = 32'hb5c0fbcf;
			6'b000011: k = 32'he9b5dba5;
			6'b000100: k = 32'h3956c25b;
			6'b000101: k = 32'h59f111f1;
			6'b000110: k = 32'h923f82a4;
			6'b000111: k = 32'hab1c5ed5;
			6'b001000: k = 32'hd807aa98;
			6'b001001: k = 32'h12835b01;
			6'b001010: k = 32'h243185be;
			6'b001011: k = 32'h550c7dc3;
			6'b001100: k = 32'h72be5d74;
			6'b001101: k = 32'h80deb1fe;
			6'b001110: k = 32'h9bdc06a7;
			6'b001111: k = 32'hc19bf174;
			6'b010000: k = 32'he49b69c1;
			6'b010001: k = 32'hefbe4786;
			6'b010010: k = 32'h0fc19dc6;
			6'b010011: k = 32'h240ca1cc;
			6'b010100: k = 32'h2de92c6f;
			6'b010101: k = 32'h4a7484aa;
			6'b010110: k = 32'h5cb0a9dc;
			6'b010111: k = 32'h76f988da;
			6'b011000: k = 32'h983e5152;
			6'b011001: k = 32'ha831c66d;
			6'b011010: k = 32'hb00327c8;
			6'b011011: k = 32'hbf597fc7;
			6'b011100: k = 32'hc6e00bf3;
			6'b011101: k = 32'hd5a79147;
			6'b011110: k = 32'h06ca6351;
			6'b011111: k = 32'h14292967;
			6'b100000: k = 32'h27b70a85;
			6'b100001: k = 32'h2e1b2138;
			6'b100010: k = 32'h4d2c6dfc;
			6'b100011: k = 32'h53380d13;
			6'b100100: k = 32'h650a7354;
			6'b100101: k = 32'h766a0abb;
			6'b100110: k = 32'h81c2c92e;
			6'b100111: k = 32'h92722c85;
			6'b101000: k = 32'ha2bfe8a1;
			6'b101001: k = 32'ha81a664b;
			6'b101010: k = 32'hc24b8b70;
			6'b101011: k = 32'hc76c51a3;
			6'b101100: k = 32'hd192e819;
			6'b101101: k = 32'hd6990624;
			6'b101110: k = 32'hf40e3585;
			6'b101111: k = 32'h106aa070;
			6'b110000: k = 32'h19a4c116;
			6'b110001: k = 32'h1e376c08;
			6'b110010: k = 32'h2748774c;
			6'b110011: k = 32'h34b0bcb5;
			6'b110100: k = 32'h391c0cb3;
			6'b110101: k = 32'h4ed8aa4a;
			6'b110110: k = 32'h5b9cca4f;
			6'b110111: k = 32'h682e6ff3;
			6'b111000: k = 32'h748f82ee;
			6'b111001: k = 32'h78a5636f;
			6'b111010: k = 32'h84c87814;
			6'b111011: k = 32'h8cc70208;
			6'b111100: k = 32'h90befffa;
			6'b111101: k = 32'ha4506ceb;
			6'b111110: k = 32'hbef9a3f7;
			6'b111111: k = 32'hc67178f2;
		endcase
	end
endmodule



module sha256_chunk(
		input wire clk, input wire [511:0] data, input wire [255:0] V_in, output wire [255:0] hash
	);
	/*
	design choices:
	select parts of data via shifter or by muxing
	use hash output as temp storage
	*/
	
	function [31:0] rotate (input [31:0] data, input [4:0] shift);
		// from http://stackoverflow.com/questions/6316653/defining-a-rightrotate-function-with-non-fixed-rotation-length/6317189#6317189
		reg [63:0] tmp;
		begin
		  tmp = {data, data} >> shift;
		  rotate = tmp[31:0];
		end
	endfunction
	function [31:0] flipbytes (input [31:0] data);
		flipbytes = {data[7:0], data[15:8], data[23:16], data[31:24]};
	endfunction
	
	// State:
	reg [255:0] V;
	reg [31:0] R[7:0]; // R[0] through R[7] represent a through h
	reg [31:0] w[15:0];
	// round computation
	// nw and nR are the computation of w and R for the next round.
	reg [31:0] nw, nR[7:0], s0, s1, S1, ch, temp1, S0, maj, temp2;
	wire [31:0] k;
	karray karray(.idx(roundnum), .k(k));
	
	// On round i, we calculate nw=w[i+16].


	assign hash[31:0] = V[31:0] + nR[0];
	assign hash[63:32] = V[63:32] + nR[1];
	assign hash[95:64] = V[95:64] + nR[2];
	assign hash[127:96] = V[127:96] + nR[3];
	assign hash[159:128] = V[159:128] + nR[4];
	assign hash[191:160] = V[191:160] + nR[5];
	assign hash[223:192] = V[223:192] + nR[6];
	assign hash[255:224] = V[255:224] + nR[7];
	
	reg [5:0] roundnum = 0;
	
	always @(*) begin
		s0 = rotate(w[1], 7) ^ rotate(w[1], 18) ^ (w[1] >> 3);
		s1 = rotate(w[14], 17) ^ rotate(w[14], 19) ^ (w[14] >> 10);
		nw = w[0] + s0 + w[9] + s1;
		
		S1 = rotate(R[4], 6) ^ rotate(R[4], 11) ^ rotate(R[4], 25);
		ch = (R[4] & R[5]) ^ ((~R[4]) & R[6]);
		temp1 = R[7] + S1 + ch + k + w[0];
		S0 = rotate(R[0], 2) ^ rotate(R[0], 13) ^ rotate(R[0], 22);
		maj = (R[0] & R[1]) ^ (R[0] & R[2]) ^ (R[1] & R[2]);
		temp2 = S0 + maj;
		
		nR[7] = R[6];
		nR[6] = R[5];
		nR[5] = R[4];
		nR[4] = R[3] + temp1;
		nR[3] = R[2];
		nR[2] = R[1];
		nR[1] = R[0];
		nR[0] = temp1 + temp2;
	end

	always @(posedge clk) begin
		if (roundnum == 6'b111111) begin
			V <= V_in;
			R[0] <= V_in[31:0];
			R[1] <= V_in[63:32];
			R[2] <= V_in[95:64];
			R[3] <= V_in[127:96];
			R[4] <= V_in[159:128];
			R[5] <= V_in[191:160];
			R[6] <= V_in[223:192];
			R[7] <= V_in[255:224];
			
			w[0] <= flipbytes(data[31:0]);
			w[1] <= flipbytes(data[63:32]);
			w[2] <= flipbytes(data[95:64]);
			w[3] <= flipbytes(data[127:96]);
			w[4] <= flipbytes(data[159:128]);
			w[5] <= flipbytes(data[191:160]);
			w[6] <= flipbytes(data[223:192]);
			w[7] <= flipbytes(data[255:224]);
			w[8] <= flipbytes(data[287:256]);
			w[9] <= flipbytes(data[319:288]);
			w[10] <= flipbytes(data[351:320]);
			w[11] <= flipbytes(data[383:352]);
			w[12] <= flipbytes(data[415:384]);
			w[13] <= flipbytes(data[447:416]);
			w[14] <= flipbytes(data[479:448]);
			w[15] <= flipbytes(data[511:480]);
		end else begin
			R[0] <= nR[0];
			R[1] <= nR[1];
			R[2] <= nR[2];
			R[3] <= nR[3];
			R[4] <= nR[4];
			R[5] <= nR[5];
			R[6] <= nR[6];
			R[7] <= nR[7];
			
			w[0] <= w[1];
			w[1] <= w[2];
			w[2] <= w[3];
			w[3] <= w[4];
			w[4] <= w[5];
			w[5] <= w[6];
			w[6] <= w[7];
			w[7] <= w[8];
			w[8] <= w[9];
			w[9] <= w[10];
			w[10] <= w[11];
			w[11] <= w[12];
			w[12] <= w[13];
			w[13] <= w[14];
			w[14] <= w[15];
			w[15] <= nw;
		end
		roundnum <= roundnum + 1'b1;
	end

endmodule
