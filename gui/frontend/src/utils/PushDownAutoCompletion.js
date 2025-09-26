import { AutoCompletion } from "petrel";

class PushDownAutoCompletion extends AutoCompletion {
    vocab = new Set();

    push(word) {
        this.vocab.add(word)
    }

    push_list(words) {
        words.forEach((word) => this.vocab.add(word))
    }

    pop(word) {
        let del_status = this.vocab.delete(word)
        console.assert(del_status, `failed to pop the word: ${word} from autocomplete list`)
    }

    autoComplete(word, editor){
        let completions = []
        console.log(editor)
        if (word == "")
            return completions
        this.vocab.forEach((suggestion) => {
            let suggestionLower = suggestion.toLowerCase()
            if (suggestionLower.startsWith(word)) {
                completions.push({
                    text: suggestion, // The text shown on the autocompletion menu
                    type: 'loc_type',
                    replace: ()=> suggestion // The current word will be replaced with myExample 
                })
            }
        })
        return completions
    }
}

export default PushDownAutoCompletion;
