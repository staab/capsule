const when = (v, f) => v && f(v)

const $ = selector => document.querySelector(selector)

const $$ = selector => document.querySelectorAll(selector)

const $clear = selector => {
  const node = $(selector)

  while (node.firstChild) {
    node.removeChild(node.firstChild)
  }

  return node
}

const isVisible = $el => {
  var {bottom, top} = $el.getBoundingClientRect()
  var viewHeight = Math.max(document.documentElement.clientHeight, window.innerHeight)

  return !(bottom < 0 || top - viewHeight >= 0)
}
