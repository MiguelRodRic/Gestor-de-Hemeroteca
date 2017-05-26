#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, \
        request, redirect, url_for, flash, jsonify
app = Flask(__name__)

FAKE_DATABASE = [
    {"id": 0,
     "msg":  """Miré los muros de la patria mía,
        si un tiempo fuertes, ya desmoronados,
        de la carrera de la edad cansados,
        por quien caduca ya su valentía."""
    },
    {"id": 1,
     "msg":  """Salíme al campo, vi que el sol bebía
        los arroyos del hielo desatados;
        y del monte quejosos los ganados,
        que con sombras hurtó la luz al día."""
    },
    {"id": 2,
     "msg":  """Entré en mi casa: vi que amancillada
        de anciana habitación era despojos;
        mi báculo más corvo, y menos fuerte."""
    },
    {"id": 3,
     "msg":  """Vencida de la edad sentí mi espada,
        y no hallé cosa en qué poner los ojos
        que no fuese recuerdo de la muerte."""
    },
    {"id": 4,
     "msg":  """¡Cómo de entre mis manos te resbalas!
        ¡Oh, cómo te deslizas, edad mía!
        ¡Qué mudos pasos traes, oh muerte fría,
        pues con callado pie todo lo igualas!"""
    },
    {"id": 5,
     "msg":  """Feroz de tierra el débil muro escalas,
        en quien lozana juventud se fía;
        mas ya mi corazón del postrer día
        atiende el vuelo, sin mirar las alas."""
    },
    {"id": 6,
     "msg":  """¡Oh condición mortal! ¡Oh dura suerte!
        ¡Que no puedo querer vivir mañana,
        sin la pensión de procurar mi muerte!"""
    },
    {"id": 7,
     "msg":      """Cualquier instante de la vida humana
        es nueva ejecución, con que me advierte
        cuán frágil es, cuán mísera, cuán vana."""
    },
]


@app.route('/')
def index():
    # Some silly pre-processing
    summaries = []
    for entry in FAKE_DATABASE:
        summaries.append({"id": entry["id"], 
                     "summary": entry["msg"].splitlines()[0].upper() })
    return render_template('index.html', summaries=summaries)


@app.route('/showFull/<int:id>')
def showFull(id):
    msg = FAKE_DATABASE[id]["msg"]
    msg = msg.replace("\n", "<br />")
    return render_template('showFull.html', msg=msg)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)
