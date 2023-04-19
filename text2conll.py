import re

reurl = re.compile(
	r'''(https?://|\w+@)?[\w\d\%\.]*\w\w\.\w\w[\w\d~/\%\#]*(\?[\w\d~/\%\#]+)*''', 
	re.U+re.M+re.I)
# combinations of numbers:
respacenum = re.compile(
	r'\d+[ ,.]+[0-9 ,.]*\d+'
)
# regex to match escapes \number\ used for special words:
rerematch = re.compile(
	r'\\\d+\\'
)

def tokenize(	text, 
	     		sent_ends='.;!?\\n', 
	     		new_sent_upper=".!?", 
				char_in_word='_-',
				glue_left="'~", 
				glue_right="",
				whole_words="aujourd'hui l'on etc. Mr. M. Nr. N° ;) ;-)",
				special_suffix="n't -je -tu -il -elle -on -nous -vous -ils -ils -elles -y -t-il -t-elle -t-ils -t-ils -t-on",
				keep_url=True, 
				combine_numbers=True, 
				sent_cut="", 
				escape = '____',
				sent_not_cut="§§§", 
				):
	"""
	text: 
		Text a transformer en Conll
	sent_ends='.;!?\\n'
		These characters end a sentence backslach escapes should be double escaped like \\n
	new_sent_upper=".!?"
		If not empty, these characters end a sentence only if the following character is upper case, should be a subset of sent_ends
	char_in_word='_-', 
		Characters that should be treated as letters inside words
	glue_left="'~", 
		Cut token after these characters 
	glue_right="" 
		Cut token before these characters 
	whole_words="aujourd'hui l'on etc. Mr. M. Nr. N° ;) ;-)", 
		Keep these space-separated words as one tokens
	special_suffix="n't -je -tu -il -elle -on -nous -vous -ils -ils -elles -y -t-il -t-elle -t-ils -t-ils -t-on",
		Keep these space-separated suffixes as separate tokens
	keep_url=True, 
		Look for URLs and keep them together
	combine_numbers=True, 
		Spaces, commas, and points between numbers are grouped together such as 999 349
	sent_cut="", 
	 	A unique word or sequence where cutting should be done. if set, sent_ends is ignored
	escape = '____', 
		No need to change this. should be letters (\w) used to escape internally. 
		Should not appear anywhere in the text
	sent_not_cut="§§§", # symbols that have been placed after the potential sent_ends that should not end the sentence. 
		This should be a unique symbol not appearing anywhere naturally in the text as it will be removed from the text.
		for example use sent_not_cut="§§§"
	"""

	# replacing words that have to remain untouched
	whole_words = whole_words.strip().split()
	special_suffix = special_suffix.strip()
	num_dot = (escape+'{}'+escape).format('NUMBERDOT')
	space_after_esc = (escape+'{}'+escape).format('NOSPACEAFTER')
	ind = 0
	ntext = text
	for w in whole_words: 
		ntext = ntext.replace(w,'\\{ind}\\'.format(ind=ind))
		ind +=1
	if special_suffix:
		respecial_suffix = re.compile(r'({})\b'.format('|'.join(special_suffix.split())))
		for m in respecial_suffix.finditer(ntext):
			ntext = ntext.replace(m.group(0),'\\{ind}\\'.format(ind=ind))
			whole_words += [m.group(0)]
			ind +=1
	if keep_url:
		for murl in reurl.finditer(ntext):
			ntext = ntext.replace(murl.group(0),'\\{ind}\\'.format(ind=ind))
			whole_words += [murl.group(0)]
			ind +=1
	if combine_numbers:
		for mnum in respacenum.finditer(ntext):
			ntext = ntext.replace(mnum.group(0),'\\{ind}\\'.format(ind=ind))
			whole_words += [mnum.group(0)]
			ind +=1

	# replace "the 2. guy" by "the 2___NUMDOT___ guy":
	re_num_dot = re.compile(r'\b(\d+)\.(?! [0-9A-ZÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÄËÏÖÜÃÑÕÆÅÐÇØ])') # num followed by . not followed by upper case
	ntext = re_num_dot.sub(r'\1'+num_dot, ntext)
	# now we split into sentences:
	if sent_cut:
		sents = ntext.split(sent_cut)
	else:
		if new_sent_upper:
			sent_ends_nopoint = re.sub(r'[{new_sent_upper}]+'.format(new_sent_upper=new_sent_upper),'', sent_ends)
			if sent_not_cut:
				re_sent_bounds = re.compile(
					'(([{sent_ends_nopoint}]+(?!{sent_not_cut})\s*)|([{sent_ends}]+(?!{sent_not_cut})\s*(?=[0-9\\\A-ZÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÄËÏÖÜÃÑÕÆÅÐÇØ])))'.format(
								sent_ends_nopoint=sent_ends_nopoint, 
								sent_ends=new_sent_upper.replace('.','\.'),
								sent_not_cut=sent_not_cut), re.U+re.M)
			else:
				re_sent_bounds = re.compile(
					'(([{sent_ends_nopoint}]+\s*)|([{sent_ends}]+\s*(?=[0-9\\\A-ZÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÄËÏÖÜÃÑÕÆÅÐÇØ])))'.format(
								sent_ends_nopoint=sent_ends_nopoint, 
								sent_ends=new_sent_upper.replace('.','\.'),
								sent_not_cut=sent_not_cut), re.U+re.M)
		else:
			if sent_not_cut:
				re_sent_bounds = re.compile(
					'([{sent_ends}](?!{sent_not_cut})+\s*)'.format(sent_ends=sent_ends, 
						    sent_not_cut=sent_not_cut), re.U+re.M)
			else:
				re_sent_bounds = re.compile(
					'([{sent_ends}]+\s*)'.format(sent_ends=sent_ends), re.U+re.M)
		
		doubsents = re_sent_bounds.split(ntext)+['']
		sents = []
		for i in range(0, len(doubsents), 2):
			if doubsents[i] and doubsents[i+1]:
				sents += [(doubsents[i].replace(sent_not_cut,'') + (doubsents[i+1] if i+1 < len(doubsents) else '')).strip()]
	
	### now we got the sents list, making the actual tokens
	retok = re.compile("(?!(\\\\d+\\\)|([\\\{} ]+))(\W+)(?!\d)".format(re.escape((char_in_word+glue_left+glue_right).replace('-','\-'))))
	reglue_left = re.compile(r'([{}])'.format(glue_left)) if glue_left else None
	reglue_right = re.compile(r'([{}])'.format(glue_right)) if glue_right else None
	stoks = {}
	def simplerematchreplace(matchobj): # used to reconstruct the sentence
		return whole_words[int(matchobj.group(0)[1:-1])]
	def rematchreplace(matchobj): # used to build the correct tokens
		if special_suffix and respecial_suffix.match(whole_words[int(matchobj.group(0)[1:-1])]):
			return space_after_esc+whole_words[int(matchobj.group(0)[1:-1])]
		return whole_words[int(matchobj.group(0)[1:-1])]

	for si,s in enumerate(sents):
		rs = rerematch.sub(simplerematchreplace,s.replace(num_dot,'.'))
		if glue_left: s = reglue_left.sub(r'\1 ', s)
		if glue_right: s = reglue_right.sub(r' \1', s)
		s = retok.sub(r'{}\3 '.format(space_after_esc), s) # adding the additional spaces
		toks = []
		spaceafters = []
		for t in s.split():
			t = t.replace(num_dot,'.')
			ts = rerematch.sub(rematchreplace,t) if rerematch.search(t) else t
			tsl = [tt for tt in ts.split(space_after_esc) if tt] 
			toks+= tsl
			spaceafters += [ii==len(tsl)-1 for ii,tt in enumerate(tsl)]
		stoks[(si,rs)] = list(zip(toks,spaceafters)) # 'si' makes keys unique and allows duplicate sentences
	return stoks


def conllize(sent2toks,id='my_sample',start=1):
    conlls=[]
    for (si,s),toksas in sent2toks.items():
        conllines=[
            '# sent_id = {id}__{ind}'.format(id=id,ind=start),
            '# text = {s}'.format(s=s)
        ]
        for i,(tok,sa) in enumerate(toksas):
            li = '{ind}\t{tok}\t_\t_\t_\t_\t_\t_\t_\t{spac}\t'.format(ind=i+1,tok=tok,spac='_' if sa else 'SpaceAfter=No')
            conllines+=[li]
        conlls+=['\n'.join(conllines)]
        start+=1
    return '\n\n'.join(conlls)+'\n'


if __name__ == "__main__":
    text = """Voici le test N° 17. C'est quand-même 
    bête, tout ça, aujourd'hui, avec le la~ lave-linge etc., peu importe ce que l'on dit sur https://blöd.com!!! T'en dis quoi, toi ;) ;-) ? Vas-y ! Ouais, M. le professeur Nr. 2. J'y crois à 100,00% !
    This is a 2. type of sample text! It contains (different) types of punctuation. 
    How to split it? Let's see; this is another example: not split here. Split Here!123 also works. but here it won't split if new_sent_upper is set.
    H_ello! regex-fan, this is a $$-test. What do you think???!!
    """
    sent2toks = tokenize(text)
    # print(sent2toks)
    conll = conllize(sent2toks)
    open('test.conllu','w').write(conll)
    # one liner:
    # open('test.conllu','w').write(conllize(tokenize(text)))