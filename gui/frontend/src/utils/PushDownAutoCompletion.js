import { AutoCompletion } from "petrel";

class PushDownAutoCompletion extends AutoCompletion {
  dynamic_vocab = new Set();
  statis_vocab = ["distance", "over", "landscape"]; // promis specific relation

  push(word) {
    this.dynamic_vocab.add(word);
  }

  push_list(words) {
    words.forEach((word) => this.dynamic_vocab.add(word));
  }

  pop(word) {
    let del_status = this.dynamic_vocab.delete(word);
    console.assert(
      del_status,
      `failed to pop the word: ${word} from autocomplete list`,
    );
  }

  flush() {
    this.dynamic_vocab.clear();
  }

  replace(oldWord, newWord) {
    this.dynamic_vocab.delete(oldWord);
    this.dynamic_vocab.add(newWord);
  }

  // eslint-disable-next-line no-unused-vars
  autoComplete(word, editor) {
    let completions = [];
    if (word == "") return completions;
    this.statis_vocab.forEach((suggestion) => {
      let suggestionLower = suggestion.toLowerCase();
      if (suggestionLower.startsWith(word)) {
        completions.push({
          text: suggestion, // The text shown on the autocompletion menu
          type: "relation",
          replace: () => suggestion, // The current word will be replaced with myExample
        });
      }
    });
    this.dynamic_vocab.forEach((suggestion) => {
      let suggestionLower = suggestion.toLowerCase();
      if (suggestionLower.startsWith(word)) {
        completions.push({
          text: suggestion, // The text shown on the autocompletion menu
          type: "loc_type",
          replace: () => suggestion, // The current word will be replaced with myExample
        });
      }
    });
    return completions;
  }
}

export default PushDownAutoCompletion;
