"""Explain the existing flat runs and the derived Schwarzschild coordinates.

No additional PDE experiment is run here. The field pictures reconstruct the
single computed Fourier mode from its saved modal amplitude. The coordinate
diagram is an analytic illustration, not a Schwarzschild field simulation.
"""

import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/flat'
BLUE='#245b83'
AMBER='#bd7642'
GRAY='#81909e'


def save(figure,path):
    figure.savefig(path.with_suffix('.pdf'),bbox_inches='tight')
    figure.savefig(path.with_suffix('.webp'),bbox_inches='tight',dpi=200,
                   pil_kwargs={'lossless':True,'method':6})
    plt.close(figure)


def inventory(config):
    cases=sorted(set([(config['dispersion_N'],j) for j in config['dispersion_modes']]
                     +[(n,config['convergence_mode']) for n in config['convergence_N']]))
    assert len(cases)==7
    lines=[r'\begin{tabular}{lrrl}',r'\toprule',
           r'Ejecución & Puntos $N$ & Modo $j$ & Comprobación \\',r'\midrule']
    for n,j in cases:
        dispersion=n==config['dispersion_N'] and j in config['dispersion_modes']
        convergence=j==config['convergence_mode'] and n in config['convergence_N']
        purpose='Dispersión y refinamiento' if dispersion and convergence else ('Dispersión' if dispersion else 'Refinamiento')
        lines.append(r'\texttt{N'+str(n)+r'\_j'+str(j)+'} & '+str(n)+' & '+str(j)+' & '+purpose+r' \\')
    lines += [r'\bottomrule',r'\end{tabular}']
    (OUT/'run_inventory.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def standing_wave(config):
    trace=np.genfromtxt(OUT/'traces/N256_j2.csv',delimiter=',',names=True)
    time=trace['t_hat'];modal=trace['a_numeric']
    x=np.linspace(0,config['L_hat'],config['dispersion_N']+1)
    basis=np.cos(2*x)
    period=2*math.pi/math.sqrt(4+config['mu_hat']**2)
    figure=plt.figure(figsize=(7,6.2),layout='constrained')
    grid=figure.add_gridspec(3,2,height_ratios=[1,1,1.15])
    for index,target in enumerate([0,period/4,period/2,3*period/4]):
        k=int(np.argmin(abs(time-target)))
        ax=figure.add_subplot(grid[index//2,index%2])
        ax.axhline(0,color='#d2d9df',lw=.8)
        ax.plot(x,basis,color='#c4cdd5',lw=1,ls='--')
        ax.plot(x,modal[k]*basis,color=BLUE if modal[k]>=0 else AMBER,lw=1.8)
        ax.set(xlim=(0,2*math.pi),ylim=(-1.18,1.18),
               title=f'Time = {time[k]:.2f}; modal value = {modal[k]:+.3f}',
               ylabel=r'$\widehat\Phi$',xlabel=r'$\widehat x$')
        ax.set_xticks([0,math.pi,2*math.pi],['0',r'$\pi$',r'$2\pi$'])
    ax=figure.add_subplot(grid[2,:])
    ax.plot(time,modal,color=BLUE,lw=1.3,label='Recorded field at x = 0')
    for value in [-1,1]:ax.axhline(value,color=GRAY,ls='--',lw=.8)
    ax.set(xlim=(0,20),ylim=(-1.25,1.25),xlabel=r'$\widehat t$',ylabel=r'$a_2(\widehat t)$',
           title='Changing sign is not decay: the envelope stays at +/-1')
    ax.legend(loc='lower left',fontsize=7,framealpha=.95)
    save(figure,OUT/'figures/field_explained')
    export_animation(x,basis,time,modal)


def export_animation(x,basis,time,modal):
    figure,axes=plt.subplots(2,1,figsize=(7.6,6.4),dpi=100)
    figure.subplots_adjust(left=.12,right=.96,top=.83,bottom=.17,hspace=.48)
    figure.suptitle('A standing field in flat spacetime',x=.12,ha='left',y=.97,fontsize=19)
    figure.text(.12,.915,'One of seven runs | N = 256 | j = 2 | mass parameter = 0.7',fontsize=10,color='#526579')
    figure.text(.12,.055,'Periodic boundaries; no damping term.\nThe curve crosses zero, but the envelope does not shrink.',
                fontsize=10,color='#526579',linespacing=1.6)
    spatial,signal=axes
    spatial.plot(x,basis,'--',color='#b9c5cf',lw=1,label='Initial profile')
    field_line,=spatial.plot(x,modal[0]*basis,color=BLUE,lw=2,label='Reconstructed computed field')
    spatial.axhline(0,color='#d5dce2',lw=.8)
    spatial.set(xlim=(0,2*math.pi),ylim=(-1.2,1.2),ylabel=r'$\widehat\Phi$',xlabel=r'$\widehat x$',
                title='Field across the periodic interval')
    spatial.set_xticks([0,math.pi,2*math.pi],['0',r'$\pi$',r'$2\pi$'])
    spatial.legend(loc='upper right',fontsize=7)
    signal.plot(time,modal,color=BLUE,lw=1.4)
    for value in [-1,1]:signal.axhline(value,color=GRAY,lw=.8,ls='--')
    cursor=signal.axvline(time[0],color=AMBER,lw=1.2)
    point,=signal.plot(time[0],modal[0],'o',color=AMBER,ms=5)
    signal.set(xlim=(0,20),ylim=(-1.25,1.25),xlabel=r'$\widehat t$',ylabel=r'$a_2(\widehat t)$',
               title='Field at x = 0; dashed levels show the fixed envelope')
    clock=figure.text(.96,.87,'',ha='right',fontsize=12,color=BLUE)
    images=[]
    indices=np.unique(np.argmin(abs(time[:,None]-np.linspace(0,20,121)[None,:]),axis=0))
    for k in indices:
        field_line.set_ydata(modal[k]*basis)
        cursor.set_xdata([time[k],time[k]]);point.set_data([time[k]],[modal[k]])
        clock.set_text(f'Time = {time[k]:05.2f} / 20.00')
        figure.canvas.draw()
        images.append(Image.fromarray(np.asarray(figure.canvas.buffer_rgba())[:,:,:3].copy()))
    images[0].save(OUT/'field_evolution.gif',save_all=True,append_images=images[1:],
                   loop=0,duration=80,disposal=2,optimize=True)
    plt.close(figure)


def coordinate_diagram():
    figure,(geometry,transform)=plt.subplots(1,2,figsize=(7,3.15),layout='constrained')
    for radius in [2,4]:geometry.add_patch(Circle((0,0),radius,fill=False,edgecolor='#b2c2cf',lw=1))
    geometry.add_patch(Circle((0,0),1,color='#20354b'))
    geometry.annotate('Horizon: r = r_s',xy=(.7,.7),xytext=(1.4,3.0),fontsize=8,
                      arrowprops={'arrowstyle':'-','color':BLUE},color=BLUE)
    geometry.annotate('',xy=(3.9,0),xytext=(1.05,0),arrowprops={'arrowstyle':'->','color':BLUE})
    geometry.text(2.3,.28,'r',color=BLUE,fontsize=10)
    geometry.text(-3.8,-3.3,'Exterior: r > r_s',fontsize=9,color=BLUE)
    geometry.set(xlim=(-4.6,4.6),ylim=(-4.2,4.3),aspect='equal',title='The exterior coordinate domain')
    geometry.axis('off')
    radius=np.r_[1+np.geomspace(1e-5,.2,300),np.linspace(1.2,6,400)]
    tortoise=radius+np.log(radius-1)
    transform.plot(radius,tortoise,color=BLUE,lw=1.8)
    transform.axvline(1,color=GRAY,ls='--',lw=.8)
    transform.axhline(0,color='#d3dce3',lw=.7)
    transform.annotate(r'$r_*\to-\infty$',xy=(1.02,-7.5),xytext=(2,-6.4),
                       arrowprops={'arrowstyle':'->','color':GRAY},fontsize=9,color=BLUE)
    transform.set(xlim=(.75,6),ylim=(-8.5,8),xlabel=r'$r/r_s$',ylabel=r'$r_*/r_s$',
                  title='The tortoise coordinate')
    transform.text(.96,.06,'Coordinate illustration\nNo field evolution is shown',transform=transform.transAxes,
                   ha='right',fontsize=7,color='#526579')
    save(figure,ROOT/'report/figures/schwarzschild_coordinates')


def create_visuals(config=None):
    if config is None:
        from run_flat_validation import CONFIG
        config=CONFIG
    with plt.rc_context({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':9,
        'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#a7b6c3',
        'axes.labelcolor':'#344b61','xtick.color':'#526579','ytick.color':'#526579','pdf.fonttype':42}):
        inventory(config);standing_wave(config);coordinate_diagram()
    print('Seven-run inventory, flat-field explanation, animation and coordinate illustration generated.',flush=True)


if __name__=='__main__':
    create_visuals()
