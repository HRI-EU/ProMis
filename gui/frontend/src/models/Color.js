import Enum from './enum.js';

export default class Color extends Enum {
	
	constructor(name, hexString){
		super(name);
		this.hexString = hexString;
	}
	
	static randomHex(){
		const letter = "0123456789ABCDEF";

		let color = "#";

		for (var i = 0; i < 6; i++){
			color = color + letter[Math.floor(Math.random() * 16)];
		}
		return color;
	}

	static custom(colorHexString) {
		return Color.forHexString(colorHexString);
	}
	
	static forHexString(colorHexString) {
		for(let color of this.values){
			if(color.hexString === colorHexString){
				return color;
			}
		}

		if(colorHexString){
			if(colorHexString[0] === '#' && colorHexString.length === 7){
				return new Color('custom', colorHexString);
			} else {
				throw new Error('Invalid color hex string: ' + colorHexString);
			}
		} else {
			return Color.black;
		}
	}
	
	toString(){
		if(this.name !== 'custom'){
			return this.name;
		} else {
			return "custom('" + this.hexString + "')";
		}		
	}
	
	static get baseValues(){
			
		return [	//source: https://de.wikipedia.org/wiki/Hilfe:Farbtabelle		
			Color.black,
			Color.blue,
			Color.cyan,
			Color.lime,
            Color.magenta,
			Color.red,
			Color.white,
			Color.yellow
		];
	}
	
	static get simpleValues(){
			
		return [  
			//sources: 
			//https://simple.wikipedia.org/wiki/List_of_colors
		
            //Color.amaranth,
			//Color.amber,
			//Color.amethyst,
			//Color.apricot,			
			Color.aqua,
			Color.aquamarine,
			//Color.azure,
			
			//Color.babyBlue,
			//Color.beige,
			Color.bisque,
			Color.black, 
			Color.blue, 
			//Color.brickRed,	
			//Color.blueGreen,
			Color.blueViolet,
			//Color.blush,
			//Color.bronze,
			Color.brown,
			//Color.burgundy,
			//Color.byzantium,
			
			//Color.carmine,
			//Color.cerise,
			//Color.cerulean,
			//Color.champagne,
			//Color.chartreuseGreen,
			Color.chocolate,
			//Color.cobaltBlue,
			//Color.coffee,
			//Color.copper,
			Color.coral,
			//Color.cornsilk,
			Color.crimson,
			Color.cyan, 			
			
			//Color.desertSand,
			Color.dodgerBlue,
			
			//Color.electricBlue,
			//Color.emerald,
			//Color.erin,
			
			Color.fireBrick,
			Color.forestGreen,
			Color.fuchsia,
			
			Color.gold,			
			Color.gray, 
			//Color.grey,
			Color.green,

			//Color.harlequin,
             
            Color.indianRed,
			Color.indigo,
			//Color.ivory,
			
			//Color.jade,
			//Color.jungleGreen,

			Color.khaki,
			
			Color.lavender,
			//Color.lemon,
			//Color.lilac,
			Color.lime,
            Color.linen,		
			
			Color.magenta,
            Color.maroon,
            //Color.mauve,
            Color.moccasin,				
			
			Color.navy, 
			
			//Color.ochre,
			Color.olive, 
			Color.orange,
			Color.orangeRed,
			Color.orchid,

			//Color.peach,
			//Color.pear,
			//Color.periwinkle,
			//Color.persianBlue,	
			Color.peru,
			Color.pink,
			Color.plum,
			//Color.prussianBlue,
			//Color.puce,
			Color.purple, 
			
			//Color.raspberry,
			Color.red, 
			//Color.redViolet,
			//Color.rose,
			//Color.ruby,
			
			Color.salmon,
			//Color.sangria,
			//Color.sapphire,
			//Color.scarlet,
			Color.sienna,
			Color.silver,
			Color.slateGray,
            //Color.snow,
			//Color.springBud,
			Color.springGreen,
			
            Color.tan,	
			//Color.taupe,
			Color.teal,
            Color.thistle,
            Color.tomato,
            Color.turquoise,

			//Color.ultramarine,

			//Color.viridian,		
            Color.violet,
			
            Color.wheat,			
			Color.white, 
			
			Color.yellow,			
		];
	}	
	
}




/*Notes from https://www.cssportal.com/css3-color-names/:

    fuchsia has the same color code as Magenta
    aqua has the same color code as Cyan
    lightGrey is spelled with an 'e', all other grays are spelled with an 'a'
    darkGray is actually lighter than Gray
    lightPink is actually darker than Pink
*/


Color.aliceBlue = new Color('aliceBlue','#f0f8ff');
Color.antiqueWhite = new Color('antiqueWhite','#faebd7');
Color.aqua = new Color('aqua','#00ffff');
Color.aquamarine = new Color('aquamarine','#7fffd4');
Color.azure = new Color('azure','#f0ffff');

Color.beige = new Color('beige','#f5f5dc');
Color.bisque = new Color('bisque','#ffe4c4');
Color.black = new Color('black','#000000');
Color.black = new Color('black','#000000');
Color.blanchedAlmond = new Color('blanchedAlmond','#ffebcd');
Color.blue = new Color('blue','#0000ff');
Color.blueViolet = new Color('blueViolet','#8a2be2');
Color.brown = new Color('brown','#a52a2a');
Color.burlyWood = new Color('burlyWood','#deb887');

Color.cadetBlue = new Color('cadetBlue','#5f9ea0');
Color.chartreuse = new Color('chartreuse','#7fff00');
Color.chocolate = new Color('chocolate','#d2691e');
Color.coral = new Color('coral','#ff7f50');
Color.cornflowerBlue = new Color('cornflowerBlue','#6495ed');
Color.cornsilk = new Color('cornsilk','#fff8dc');
Color.crimson = new Color('crimson','#dc143c');
Color.cyan = new Color('cyan','#00ffff');

Color.darkBlue = new Color('darkBlue','#00008b');
Color.darkCyan = new Color('darkCyan','#008b8b');
Color.darkGoldenRod = new Color('darkGoldenRod','#b8860b');
Color.darkGray = new Color('darkGray','#a9a9a9');
Color.darkGreen = new Color('darkGreen','#006400');
Color.darkGrey = new Color('darkGrey','#a9a9a9');
Color.darkKhaki = new Color('darkKhaki','#bdb76b');
Color.darkMagenta = new Color('darkMagenta','#8b008b');
Color.darkOliveGreen = new Color('darkOliveGreen','#556b2f');
Color.darkOrange = new Color('darkOrange','#ff8c00');
Color.darkOrchid = new Color('darkOrchid','#9932cc');
Color.darkRed = new Color('darkRed','#8b0000');
Color.darkSalmon = new Color('darkSalmon','#e9967a');
Color.darkSeaGreen = new Color('darkSeaGreen','#8fbc8f');
Color.darkSlateBlue = new Color('darkSlateBlue','#483d8b');
Color.darkSlateGray = new Color('darkSlateGray','#2f4f4f');
Color.darkSlateGrey = new Color('darkSlateGrey','#2f4f4f');
Color.darkTurquoise = new Color('darkTurquoise','#00ced1');
Color.darkViolet = new Color('darkViolet','#9400d3');
Color.deepPink = new Color('deepPink','#ff1493');
Color.deepSkyBlue = new Color('deepSkyBlue','#00bfff');
Color.dimGray = new Color('dimGray','#696969');
Color.dimGrey = new Color('dimGrey','#696969');
Color.dodgerBlue = new Color('dodgerBlue','#1e90ff');

Color.fireBrick = new Color('fireBrick','#b22222');
Color.floralWhite = new Color('floralWhite','#fffaf0');
Color.forestGreen = new Color('forestGreen','#228b22');
Color.fuchsia = new Color('fuchsia','#ff00ff');

Color.gainsboro = new Color('gainsboro','#dcdcdc');
Color.ghostWhite = new Color('ghostWhite','#f8f8ff');
Color.gold = new Color('gold','#ffd700');
Color.goldenRod = new Color('goldenRod','#daa520');
Color.goldenrod = new Color('goldenrod','#daa520');
Color.gray = new Color('gray','#808080');
Color.green = new Color('green','#008000');
Color.greenYellow = new Color('greenYellow','#adff2f');
Color.grey = new Color('grey','#808080');

Color.honeyDew = new Color('honeyDew','#f0fff0');
Color.hotPink = new Color('hotPink','#ff69b4');

Color.indianRed = new Color('indianRed','#cd5c5c');
Color.indigo = new Color('indigo','#4b0082');
Color.ivory = new Color('ivory','#fffff0');

Color.khaki = new Color('khaki','#f0e68c');

Color.lavender = new Color('lavender','#e6e6fa');
Color.lavenderBlush = new Color('lavenderBlush','#fff0f5');
Color.lawnGreen = new Color('lawnGreen','#7cfc00');
Color.lemonChiffon = new Color('lemonChiffon','#fffacd');
Color.lightBlue = new Color('lightBlue','#add8e6');
Color.lightCoral = new Color('lightCoral','#f08080');
Color.lightCyan = new Color('lightCyan','#e0ffff');
Color.lightGoldenRodYellow = new Color('lightGoldenRodYellow','#fafad2');
Color.lightGray = new Color('lightGray','#d3d3d3');
Color.lightGreen = new Color('lightGreen','#90ee90');
Color.lightGrey = new Color('lightGrey','#d3d3d3');
Color.lightPink = new Color('lightPink','#ffb6c1');
Color.lightSalmon = new Color('lightSalmon','#ffa07a');
Color.lightSeaGreen = new Color('lightSeaGreen','#20b2aa');
Color.lightSkyBlue = new Color('lightSkyBlue','#87cefa');
Color.lightSlateGray = new Color('lightSlateGray','#778899');
Color.lightSlateGrey = new Color('lightSlateGrey','#778899');
Color.lightSteelBlue = new Color('lightSteelBlue','#b0c4de');
Color.lightYellow = new Color('lightYellow','#ffffe0');
Color.lime = new Color('lime','#00ff00');
Color.limeGreen = new Color('limeGreen','#32cd32');
Color.linen = new Color('linen','#faf0e6');

Color.magenta = new Color('magenta','#ff00ff');
Color.maroon = new Color('maroon','#800000');
Color.mediumAquaMarine = new Color('mediumAquaMarine','#66cdaa');
Color.mediumBlue = new Color('mediumBlue','#0000cd');
Color.mediumOrchid = new Color('mediumOrchid','#ba55d3');
Color.mediumPurple = new Color('mediumPurple','#9370db');
Color.mediumSeaGreen = new Color('mediumSeaGreen','#3cb371');
Color.mediumSlateBlue = new Color('mediumSlateBlue','#7b68ee');
Color.mediumSpringGreen = new Color('mediumSpringGreen','#00fa9a');
Color.mediumTurquoise = new Color('mediumTurquoise','#48d1cc');
Color.mediumVioletRed = new Color('mediumVioletRed','#c71585');
Color.midnightBlue = new Color('midnightBlue','#191970');
Color.mintCream = new Color('mintCream','#f5fffa');
Color.mistyRose = new Color('mistyRose','#ffe4e1');
Color.moccasin = new Color('moccasin','#ffe4b5');

Color.navajoWhite = new Color('navajoWhite','#ffdead');
Color.navy = new Color('navy','#000080');

Color.oldLace = new Color('oldLace','#fdf5e6');
Color.olive = new Color('olive','#808000');
Color.oliveDrab = new Color('oliveDrab','#6b8e23');
Color.orange = new Color('orange','#ffa500');
Color.orangeRed = new Color('orangeRed','#ff4500');
Color.orchid = new Color('orchid','#da70d6');

Color.paleGoldenRod = new Color('paleGoldenRod','#eee8aa');
Color.paleGreen = new Color('paleGreen','#98fb98');
Color.paleTurquoise = new Color('paleTurquoise','#afeeee');
Color.paleVioletRed = new Color('paleVioletRed','#db7093');
Color.papayaWhip = new Color('papayaWhip','#ffefd5');
Color.peachPuff = new Color('peachPuff','#ffdab9');
Color.peru = new Color('peru','#cd853f');
Color.pink = new Color('pink','#ffc0cb');
Color.plum = new Color('plum','#dda0dd');
Color.powderBlue = new Color('powderBlue','#b0e0e6');
Color.purple = new Color('purple','#800080');

Color.rebeccaPurple = new Color('rebeccaPurple','#663399');
Color.red = new Color('red','#ff0000');
Color.rosyBrown = new Color('rosyBrown','#bc8f8f');
Color.royalBlue = new Color('royalBlue','#4169e1');

Color.saddleBrown = new Color('saddleBrown','#8b4513');
Color.salmon = new Color('salmon','#fa8072');
Color.sandyBrown = new Color('sandyBrown','#f4a460');
Color.seaGreen = new Color('seaGreen','#2e8b57');
Color.seaShell = new Color('seaShell','#fff5ee');
Color.seashell = new Color('seashell','#fff5ee');
Color.sienna = new Color('sienna','#a0522d');
Color.silver = new Color('silver','#c0c0c0');
Color.skyBlue = new Color('skyBlue','#87ceeb');
Color.slateBlue = new Color('slateBlue','#6a5acd');
Color.slateGray = new Color('slateGray','#708090');
Color.slateGrey = new Color('slateGrey','#708090');
Color.snow = new Color('snow','#fffafa');
Color.springGreen = new Color('springGreen','#00ff7f');
Color.steelBlue = new Color('steelBlue','#4682b4');

Color.tan = new Color('tan','#d2b48c');
Color.teal = new Color('teal','#008080');
Color.thistle = new Color('thistle','#d8bfd8');
Color.tomato = new Color('tomato','#ff6347');
Color.turquoise = new Color('turquoise','#40e0d0');

Color.violet = new Color('violet','#ee82ee');

Color.wheat = new Color('wheat','#f5deb3');
Color.white = new Color('white','#ffffff');
Color.whiteSmoke = new Color('whiteSmoke','#f5f5f5');

Color.yellow = new Color('yellow','#ffff00');
Color.yellowGreen = new Color('yellowGreen','#9acd32');

