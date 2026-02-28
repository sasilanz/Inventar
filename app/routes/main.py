from datetime import date, timedelta
from flask import Blueprint, render_template, request
from sqlalchemy import or_
from app.models.inventar import Ding, Kategorie, Tag
from app.models.standort import Zone, Raum, Gestell, Regalfach, Behaelter
from app.models.tracking import Verleih

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    from app.models.standort import Raum, Gestell, Behaelter
    from app.models.tracking import Verleih
    ausgeliehen = (Verleih.query
                   .filter_by(zurueck_am=None)
                   .order_by(Verleih.faellig_am.asc().nullslast())
                   .all())
    stats = dict(
        dinge      = Ding.query.count(),
        behaelter  = Behaelter.query.count(),
        gestelle   = Gestell.query.count(),
        raeume     = Raum.query.count(),
        ausgeliehen= len(ausgeliehen),
    )
    return render_template('index.html', stats=stats, ausgeliehen=ausgeliehen, today=date.today())


@main_bp.route('/suchen')
def suchen():
    q             = request.args.get('q', '').strip()
    kategorie_id  = request.args.get('kategorie_id', type=int)
    tag_ids       = request.args.getlist('tag_ids', type=int)
    zone_id       = request.args.get('zone_id', type=int)
    raum_id       = request.args.get('raum_id', type=int)
    gestell_id    = request.args.get('gestell_id', type=int)
    regalfach_id  = request.args.get('regalfach_id', type=int)
    behaelter_id  = request.args.get('behaelter_id', type=int)
    ausgeliehen   = request.args.get('ausgeliehen', '')
    garantie_bald = request.args.get('garantie_bald')

    gesucht = any([q, kategorie_id, tag_ids, zone_id, raum_id, gestell_id,
                   regalfach_id, behaelter_id, ausgeliehen, garantie_bald])
    dinge = []

    if gesucht:
        query = Ding.query

        # Freitext
        if q:
            query = query.filter(or_(
                Ding.name.ilike(f'%{q}%'),
                Ding.beschreibung.ilike(f'%{q}%'),
                Ding.hersteller.ilike(f'%{q}%'),
                Ding.modell.ilike(f'%{q}%'),
                Ding.seriennummer.ilike(f'%{q}%'),
            ))

        if kategorie_id:
            query = query.filter_by(kategorie_id=kategorie_id)

        for tid in tag_ids:
            query = query.filter(Ding.tags.any(id=tid))

        # Standort-Filter (von spezifisch nach allgemein)
        # Zone: alle Räume der Zone sammeln, dann wie raum_id filtern
        if not raum_id and zone_id:
            r_ids = [r.id for r in Raum.query.filter_by(zone_id=zone_id)]
            if not gestell_id and not regalfach_id and not behaelter_id:
                g_ids = [g.id for g in Gestell.query.filter(Gestell.raum_id.in_(r_ids))] if r_ids else []
                f_ids = [f.id for f in Regalfach.query.filter(Regalfach.gestell_id.in_(g_ids))] if g_ids else []
                b_ids = [b.id for b in Behaelter.query.filter(or_(
                    Behaelter.raum_id.in_(r_ids),
                    *(([Behaelter.gestell_id.in_(g_ids)]) if g_ids else []),
                    *(([Behaelter.regalfach_id.in_(f_ids)]) if f_ids else []),
                ))] if r_ids else []
                conds = []
                if r_ids: conds.append(Ding.raum_id.in_(r_ids))
                if g_ids: conds.append(Ding.gestell_id.in_(g_ids))
                if f_ids: conds.append(Ding.regalfach_id.in_(f_ids))
                if b_ids: conds.append(Ding.behaelter_id.in_(b_ids))
                if conds: query = query.filter(or_(*conds))

        if behaelter_id:
            query = query.filter(Ding.behaelter_id == behaelter_id)
        elif regalfach_id:
            b_ids = [b.id for b in Behaelter.query.filter_by(regalfach_id=regalfach_id)]
            conds = [Ding.regalfach_id == regalfach_id]
            if b_ids:
                conds.append(Ding.behaelter_id.in_(b_ids))
            query = query.filter(or_(*conds))
        elif gestell_id:
            f_ids = [f.id for f in Regalfach.query.filter_by(gestell_id=gestell_id)]
            b_ids = [b.id for b in Behaelter.query.filter(or_(
                Behaelter.gestell_id == gestell_id,
                *(([Behaelter.regalfach_id.in_(f_ids)]) if f_ids else []),
            ))]
            conds = [Ding.gestell_id == gestell_id]
            if f_ids:
                conds.append(Ding.regalfach_id.in_(f_ids))
            if b_ids:
                conds.append(Ding.behaelter_id.in_(b_ids))
            query = query.filter(or_(*conds))
        elif raum_id:
            g_ids = [g.id for g in Gestell.query.filter_by(raum_id=raum_id)]
            f_ids = [f.id for f in Regalfach.query.filter(
                Regalfach.gestell_id.in_(g_ids))] if g_ids else []
            b_ids = [b.id for b in Behaelter.query.filter(or_(
                Behaelter.raum_id == raum_id,
                *(([Behaelter.gestell_id.in_(g_ids)]) if g_ids else []),
                *(([Behaelter.regalfach_id.in_(f_ids)]) if f_ids else []),
            ))]
            conds = [Ding.raum_id == raum_id]
            if g_ids:
                conds.append(Ding.gestell_id.in_(g_ids))
            if f_ids:
                conds.append(Ding.regalfach_id.in_(f_ids))
            if b_ids:
                conds.append(Ding.behaelter_id.in_(b_ids))
            query = query.filter(or_(*conds))

        # Ausgeliehen
        if ausgeliehen == 'ja':
            query = query.filter(
                Ding.verleih_eintraege.any(Verleih.zurueck_am == None))
        elif ausgeliehen == 'nein':
            query = query.filter(
                ~Ding.verleih_eintraege.any(Verleih.zurueck_am == None))

        # Garantie läuft bald ab (innerhalb 90 Tage)
        if garantie_bald:
            query = query.filter(
                Ding.garantie_bis != None,
                Ding.garantie_bis <= date.today() + timedelta(days=90),
                Ding.garantie_bis >= date.today(),
            )

        dinge = query.order_by(Ding.name).all()

    today = date.today()
    return render_template('suchen.html',
        dinge=dinge, gesucht=gesucht,
        q=q, kategorie_id=kategorie_id, tag_ids=tag_ids,
        zone_id=zone_id, raum_id=raum_id, gestell_id=gestell_id,
        regalfach_id=regalfach_id, behaelter_id=behaelter_id,
        ausgeliehen=ausgeliehen, garantie_bald=garantie_bald,
        today=today, today_90=today + timedelta(days=90),
        kategorien=Kategorie.query.order_by(Kategorie.name).all(),
        alle_tags=Tag.query.order_by(Tag.name).all(),
        zonen=Zone.query.order_by(Zone.name).all(),
        raeume=Raum.query.join(Zone).order_by(Zone.name, Raum.name).all(),
        gestelle=Gestell.query.order_by(Gestell.name).all(),
        regalfaecher=Regalfach.query.order_by(Regalfach.bezeichnung).all(),
        behaelter=Behaelter.query.order_by(Behaelter.name).all(),
    )


@main_bp.route('/erfassen')
def erfassen():
    return render_template('erfassen.html')
