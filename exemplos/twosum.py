"""Two Sum (LeetCode 1): índices de dois números que somam o alvo.

A classe abaixo é a resposta como se cola no LeetCode. Sozinha ela não
roda nada: o LeetCode chama o método por fora. Aqui, as últimas linhas
fazem essa chamada, e é a partir delas que o visualizador acompanha.

Rode com:  xray exemplos/twosum.py
"""


class Solution(object):
    def twoSum(self, nums, target):
        """
        :type nums: List[int]
        :type target: int
        :rtype: List[int]
        """
        resultado = []
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    resultado.append(i)
                    resultado.append(j)
        return resultado


# --- o que o LeetCode faz por fora: cria a entrada e chama o método ---
nums = [2, 7, 11, 15]                      # entrada (aparece como array)
alvo = 9                                   # soma procurada
resposta = Solution().twoSum(nums, alvo)   # aqui o rastreio entra no método
print(resposta)                            # esperado: [0, 1]
