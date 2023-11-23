import { codes } from 'micromark-util-symbol';
import { addRemarkExtension } from "./helpers";


function todoSyntax() {
  return {
    name: 'todo',
    text: {
      [codes.uppercaseT]: {
        tokenize: tokenizeTodo,
      },
      [codes.lowercaseT]: {
        tokenize: tokenizeTodo,
      },
    }
  };

  function tokenizeTodo(effects, ok, nok) {
    return startT;

    function startT(code) {
      effects.enter('todo');
      effects.enter('data');
      effects.consume(code);
      return middleO;
    }
    function middleO(code) {
      if (![codes.uppercaseO, codes.lowercaseO].includes(code)) {
        return nok(code);
      }
      effects.consume(code);
      return middleDorDash;
    }
    function middleDorDash(code) {
      if (code == codes.dash) {
        effects.consume(code);
        return middleD;
      }
      return middleD(code);
    }
    function middleD(code) {
      if (![codes.uppercaseD, codes.lowercaseD].includes(code)) {
        return nok(code);
      }
      effects.consume(code);
      return endO;
    }
    function endO(code) {
      if (![codes.uppercaseO, codes.lowercaseO].includes(code)) {
        return nok(code);
      }
      effects.consume(code);
      effects.exit('data');
      effects.exit('todo');
      return ok(code);
    }
  }
}


function todoFromMarkdown() {
  return {
    enter: {
      todo: enterTodo,
    },
    exit: {
      todo: exitTodo,
    }
  };

  function enterTodo(token) {
    this.enter({type: 'todo', children: [], data: {hName: 'span', hProperties: {class: 'todo'}}}, token);
  }
  function exitTodo(token) {
    this.exit(token);
  }
}

function todoToMarkdown() {
  return {
    handlers: {
      todo,
    } 
  };

  function todo(node, _, state, safeOptions) {
    const exit = state.enter('todo');
    const value = state.containerPhrasing(node, safeOptions);
    exit();
    return value;
  }
}


export function remarkTodoMarker() {
  addRemarkExtension(this, todoSyntax(), todoFromMarkdown(), todoToMarkdown());
}
