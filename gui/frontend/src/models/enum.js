
export default class Enum {

	static get values(){
		var keys = Object.keys(this)
					.filter(key=>!key.startsWith('__'))
					.filter(key=>!(this[key] instanceof Function));		
		return keys.map(key=>this[key]);
	}	

	static get names(){
		return this.values.map((value)=>value.name);
	}

	static get importLocation(){
		return this.__importLocation;
	}

	static forName(name){
		for(var type of this.values){
			if(type.name === name){
				return type;
			}
		}

		if (type.name === "null"){
			return this.values[0]
		}
		
		throw new Error('Unknown value "' + name + '"');
	}

	static __determineImportLocation(){
		var stack = new Error().stack;
		var lastLine = stack.split('\n').pop();
		var startIndex = lastLine.indexOf('/src/');
		if(startIndex === -1){
			return 'Could not find location of Enum definition. (Only works inside /src/ folder).';
		}
		var endIndex = lastLine.indexOf('.js:') + 3;
		return lastLine.substring(startIndex, endIndex);
	}
		
	constructor(name){
		this.name = name;
		if(!this.constructor.__importLocation){
			this.constructor.__importLocation = Enum.__determineImportLocation();
		}						
	}
	
	toString(){
		return this.name;
	}



}
